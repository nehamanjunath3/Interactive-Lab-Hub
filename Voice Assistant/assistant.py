#!/usr/bin/env python3
"""
Voice AI Assistant for Raspberry Pi w/ Adafruit Mini PiTFT 1.3"
- Button A (GPIO 23): press to start recording
- Button B (GPIO 24): press to stop recording early
- MiniPiTFT display : show status and responses
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

# ── MiniPiTFT pins ────────────────────────────────────────────────────────────
BTN_A = 23
BTN_B = 24

# ── Display colours ───────────────────────────────────────────────────────────
BLACK  = (  0,   0,   0)
WHITE  = (255, 255, 255)
BLUE   = ( 30, 100, 255)
PURPLE = (150,   0, 255)
GREEN  = ( 30, 200,  80)
RED    = (220,  50,  30)
GREY   = ( 60,  60,  60)


def init_display():
    cs    = digitalio.DigitalInOut(board.CE0)
    dc    = digitalio.DigitalInOut(board.D25)
    reset = digitalio.DigitalInOut(board.D24)
    spi   = board.SPI()
    disp  = st7789.ST7789(spi, rotation=90, width=240, height=240,
                          cs=cs, dc=dc, rst=reset, baudrate=64000000)
    # Turn on backlight
    backlight = digitalio.DigitalInOut(board.D26)
    backlight.switch_to_output()
    backlight.value = True
    return disp


def init_buttons():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BTN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BTN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def btn_a_pressed():
    return GPIO.input(BTN_A) == GPIO.LOW


def btn_b_pressed():
    return GPIO.input(BTN_B) == GPIO.LOW


def show(disp, title, body="", title_color=WHITE, body_color=WHITE, bg=BLACK):
    img  = Image.new("RGB", (240, 240), bg)
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font_body  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except Exception:
        font_title = ImageFont.load_default()
        font_body  = font_title

    # Title
    draw.text((10, 10), title, font=font_title, fill=title_color)

    # Body — word-wrap to ~18 chars per line
    if body:
        y = 55
        for line in textwrap.wrap(body, width=18):
            draw.text((10, y), line, font=font_body, fill=body_color)
            y += 26
            if y > 220:
                break

    disp.image(img)


def find_input_device(pa):
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0 and "USB" in info["name"]:
            print(f"  Mic: {info['name']} (index {i})")
            return i
    return None


def record_audio(disp):
    pa          = pyaudio.PyAudio()
    input_index = find_input_device(pa)
    stream      = pa.open(format=pyaudio.paInt16, channels=CHANNELS,
                          rate=SAMPLE_RATE, input=True,
                          input_device_index=input_index,
                          frames_per_buffer=CHUNK)
    frames = []
    start  = time.time()
    show(disp, "Listening...", "Press B to stop", title_color=BLUE, bg=(0, 0, 20))

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


def transcribe(whisper_model, audio_path, disp):
    show(disp, "Transcribing...", title_color=PURPLE, bg=(10, 0, 20))
    segments, _ = whisper_model.transcribe(audio_path, language="en")
    text = " ".join(seg.text.strip() for seg in segments)
    os.unlink(audio_path)
    return text.strip()


def ask_claude(client, history, user_text, disp):
    show(disp, "Thinking...", user_text[:60], title_color=PURPLE, bg=(10, 0, 20))
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


def speak(text, disp):
    show(disp, "Claude says:", text, title_color=GREEN, bg=(0, 15, 0))
    print(f"  Claude: {text}")
    subprocess.run(["espeak-ng", "-s", "145", "-v", "en-us+f3", text], check=False)


def main():
    print("Initialising display...")
    disp = init_display()
    show(disp, "Starting up...", bg=GREY)

    print("Initialising buttons...")
    init_buttons()

    print(f"Loading Whisper '{WHISPER_MODEL}' model...")
    show(disp, "Loading AI...", "Please wait", bg=GREY)
    whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

    client  = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    history = []

    show(disp, "Ready!", "Press A to speak", title_color=GREEN, bg=BLACK)
    print("Ready! Press button A to speak. Ctrl+C to quit.")

    try:
        while True:
            if btn_a_pressed():
                # Debounce
                time.sleep(0.05)
                while btn_a_pressed():
                    time.sleep(0.05)

                audio_path = record_audio(disp)
                user_text  = transcribe(whisper_model, audio_path, disp)

                if not user_text:
                    show(disp, "Didn't hear", "Try again", title_color=RED, bg=BLACK)
                    print("  Didn't catch that")
                    time.sleep(2)
                else:
                    print(f"  You: {user_text}")
                    reply = ask_claude(client, history, user_text, disp)
                    speak(reply, disp)
                    time.sleep(0.5)

                show(disp, "Ready!", "Press A to speak", title_color=GREEN, bg=BLACK)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nBye!")
        show(disp, "Goodbye!", bg=BLACK)
        GPIO.cleanup()


if __name__ == "__main__":
    main()
