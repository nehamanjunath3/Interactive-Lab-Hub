#!/usr/bin/env python3
"""
Voice AI Assistant for Raspberry Pi w/ Adafruit Mini PiTFT 1.3"
- Button A (GPIO 23): press to start recording
- Button B (GPIO 24): press to stop recording early
- MiniPiTFT display : Inside Out emotion faces per state
- Qwiic LED stick   : colour reactions (optional)
- faster-whisper    : speech-to-text (runs locally)
- Claude Haiku      : AI responses
- espeak-ng         : text-to-speech
"""

import os
import time
import wave
import tempfile
import textwrap
import subprocess
from pathlib import Path

import pyaudio
import anthropic
import RPi.GPIO as GPIO
import board
import digitalio
from adafruit_rgb_display import st7789
from PIL import Image, ImageDraw, ImageFont
from faster_whisper import WhisperModel

# ── Config ────────────────────────────────────────────────────────────────────
SAMPLE_RATE     = 44100
CHANNELS        = 1
CHUNK           = 1024
MAX_RECORD_SECS = 8
WHISPER_MODEL   = "tiny"
CLAUDE_MODEL    = "claude-haiku-4-5-20251001"
SYSTEM_PROMPT   = (
    "You are a friendly voice assistant on a Raspberry Pi. "
    "Keep every response under 2 sentences — it'll be shown on a small screen "
    "and spoken aloud."
)

BTN_A     = 23
BTN_B     = 24
FACES_DIR = Path(__file__).parent / "faces"

# State → (face, label, label_colour, bg, led_colour)
STATES = {
    "idle":         ("joy.png",     "Press A to talk!",  (255, 220,   0), ( 20,  15,   0), (  8,   6,   0)),
    "listening":    ("fear.png",    "Listening...",      (180,  80, 255), ( 10,   0,  20), (  5,   0,  10)),
    "transcribing": ("sadness.png", "Got it, thinking!", ( 80, 140, 255), (  0,   5,  20), (  0,   2,   8)),
    "thinking":     ("sadness.png", "Thinking...",       ( 80, 140, 255), (  0,   5,  20), (  0,   2,   8)),
    "speaking":     ("excited.png", "Claude says:",      ( 60, 220, 100), (  0,  15,   5), (  0,   8,   2)),
    "error":        ("anger.png",   "Didn't catch that", (220,  60,  40), ( 20,   0,   0), (  8,   0,   0)),
}


# ── Hardware init ─────────────────────────────────────────────────────────────

def init_display():
    cs    = digitalio.DigitalInOut(board.CE0)
    dc    = digitalio.DigitalInOut(board.D25)
    reset = digitalio.DigitalInOut(board.D24)
    spi   = board.SPI()
    disp  = st7789.ST7789(spi, rotation=90, width=240, height=240,
                          cs=cs, dc=dc, rst=reset, baudrate=64000000)
    backlight = digitalio.DigitalInOut(board.D26)
    backlight.switch_to_output()
    backlight.value = True
    return disp


def init_leds():
    try:
        import qwiic_led_stick
        stick = qwiic_led_stick.QwiicLEDStick()
        if stick.is_connected():
            stick.set_all_LED_brightness(15)
            print("  LED stick connected")
            return stick
    except Exception:
        pass
    print("  LED stick not found — skipping")
    return None


def set_leds(stick, colour):
    if stick is None:
        return
    try:
        r, g, b = colour
        stick.set_all_LED_color(r, g, b)
    except Exception:
        pass


def init_buttons():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BTN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BTN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def btn_a_pressed():
    return GPIO.input(BTN_A) == GPIO.LOW


def btn_b_pressed():
    return GPIO.input(BTN_B) == GPIO.LOW


def load_fonts():
    try:
        bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        reg  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
    except Exception:
        bold = ImageFont.load_default()
        reg  = bold
    return bold, reg


# ── Display ───────────────────────────────────────────────────────────────────

def show_face(disp, fonts, stick, state, body=""):
    face_file, label, label_color, bg, led_color = STATES[state]
    bold, reg = fonts

    set_leds(stick, led_color)

    img  = Image.new("RGB", (240, 240), bg)
    draw = ImageDraw.Draw(img)

    # Face — top portion, centred
    face_path = FACES_DIR / face_file
    if face_path.exists():
        face = Image.open(face_path).convert("RGBA").resize((130, 130), Image.LANCZOS)
        img.paste(face, (55, 8), face)

    # Divider line
    draw.line([(0, 145), (240, 145)], fill=(50, 50, 50), width=1)

    # Label
    draw.text((8, 150), label, font=bold, fill=label_color)

    # Body text — word-wrapped
    if body:
        y = 178
        for line in textwrap.wrap(body, width=26):
            draw.text((8, y), line, font=reg, fill=(220, 220, 220))
            y += 21
            if y > 235:
                break

    disp.image(img)


# ── Audio ─────────────────────────────────────────────────────────────────────

def find_input_device(pa):
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0 and "USB" in info["name"]:
            print(f"  Mic: {info['name']} (index {i})")
            return i
    return None


def record_audio(disp, fonts, stick):
    pa          = pyaudio.PyAudio()
    input_index = find_input_device(pa)
    stream      = pa.open(format=pyaudio.paInt16, channels=CHANNELS,
                          rate=SAMPLE_RATE, input=True,
                          input_device_index=input_index,
                          frames_per_buffer=CHUNK)
    frames = []
    start  = time.time()
    show_face(disp, fonts, stick, "listening")

    while time.time() - start < MAX_RECORD_SECS:
        frames.append(stream.read(CHUNK, exception_on_overflow=False))
        if btn_b_pressed():
            break

    stream.stop_stream()
    stream.close()
    pa.terminate()

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(frames))
    return tmp.name


# ── AI pipeline ───────────────────────────────────────────────────────────────

def transcribe(whisper_model, audio_path, disp, fonts, stick):
    show_face(disp, fonts, stick, "transcribing")
    segments, _ = whisper_model.transcribe(audio_path, language="en")
    text = " ".join(seg.text.strip() for seg in segments)
    os.unlink(audio_path)
    return text.strip()


def ask_claude(client, history, user_text, disp, fonts, stick):
    show_face(disp, fonts, stick, "thinking", user_text[:80])
    history.append({"role": "user", "content": user_text})
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=150,
        system=SYSTEM_PROMPT,
        messages=history,
    )
    reply = response.content[0].text.strip()
    history.append({"role": "assistant", "content": reply})
    return reply


def speak(text, disp, fonts, stick):
    show_face(disp, fonts, stick, "speaking", text)
    print(f"  Claude: {text}")
    subprocess.run(["espeak-ng", "-s", "145", "-v", "en-us+f3", text], check=False)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Initialising display...")
    disp  = init_display()
    fonts = load_fonts()

    print("Initialising buttons...")
    init_buttons()

    print("Initialising LED stick...")
    stick = init_leds()

    print(f"Loading Whisper '{WHISPER_MODEL}' model...")
    show_face(disp, fonts, stick, "thinking")
    whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

    client  = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    history = []

    show_face(disp, fonts, stick, "idle")
    print("Ready! Press button A to speak. Ctrl+C to quit.")

    try:
        while True:
            if btn_a_pressed():
                time.sleep(0.05)
                while btn_a_pressed():
                    time.sleep(0.05)

                audio_path = record_audio(disp, fonts, stick)
                user_text  = transcribe(whisper_model, audio_path, disp, fonts, stick)

                if not user_text:
                    show_face(disp, fonts, stick, "error")
                    print("  Didn't catch that")
                    time.sleep(2)
                else:
                    print(f"  You: {user_text}")
                    reply = ask_claude(client, history, user_text, disp, fonts, stick)
                    speak(reply, disp, fonts, stick)
                    time.sleep(0.5)

                show_face(disp, fonts, stick, "idle")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nBye!")
        set_leds(stick, (0, 0, 0))
        show_face(disp, fonts, stick, "idle")
        GPIO.cleanup()


if __name__ == "__main__":
    main()
