#!/usr/bin/env python3
"""
Voice AI Assistant for Raspberry Pi
- Green Qwiic button (addr 0x5F): press to talk
- Red Qwiic button  (addr 0x6F): stop recording
- Qwiic LED stick                : status colors
- Qwiic OLED display             : show conversation
- faster-whisper                 : speech-to-text (runs locally)
- Gemini API                     : AI responses
- espeak-ng                      : text-to-speech
"""

import os
import time
import wave
import tempfile
import textwrap
import subprocess

import pyaudio
from google import genai
import qwiic_button
import qwiic_led_stick
import qwiic_micro_oled
from faster_whisper import WhisperModel

# ── Config ────────────────────────────────────────────────────────────────────
SAMPLE_RATE       = 16000
CHANNELS          = 1
CHUNK             = 1024
MAX_RECORD_SECS   = 15
WHISPER_MODEL     = "tiny"          # "base" is more accurate but slower on Pi
GEMINI_MODEL      = "gemini-1.5-flash"
SYSTEM_PROMPT     = (
    "You are a friendly voice assistant running on a Raspberry Pi. "
    "Keep every response under 2 sentences so it fits on a small screen "
    "and doesn't take long to read aloud."
)

# ── LED colours (r, g, b) ─────────────────────────────────────────────────────
COLOUR_OFF      = (  0,   0,   0)
COLOUR_IDLE     = (  5,   5,   5)   # dim white
COLOUR_LISTEN   = (  0,  50, 255)   # blue
COLOUR_THINK    = (128,   0, 255)   # purple
COLOUR_SPEAK    = (  0, 200,  50)   # green
COLOUR_ERROR    = (255,  30,   0)   # red-orange


def init_hardware():
    green_btn = qwiic_button.QwiicButton(address=0x5F)
    red_btn   = qwiic_button.QwiicButton(address=0x6F)
    leds      = qwiic_led_stick.QwiicLEDStick()
    oled      = qwiic_micro_oled.QwiicMicroOled()

    for dev, name in [(green_btn, "green button"), (red_btn, "red button"),
                      (leds, "LED stick"), (oled, "OLED")]:
        if not dev.is_connected():
            print(f"[WARN] {name} not detected — check wiring/address")

    oled.begin()
    return green_btn, red_btn, leds, oled


def set_leds(leds, colour):
    r, g, b = colour
    leds.set_all_led_color(r, g, b)


def pulse_leds(leds, colour, times=2):
    for _ in range(times):
        set_leds(leds, colour)
        time.sleep(0.12)
        set_leds(leds, COLOUR_OFF)
        time.sleep(0.12)


def show_oled(oled, line1, line2=""):
    oled.clear()
    wrapped = textwrap.wrap(line1, 16)[:2]
    if line2:
        wrapped += textwrap.wrap(line2, 16)[:2]
    for row, text in enumerate(wrapped[:4]):
        oled.print(text)
    oled.display()


def record_audio(leds, oled, red_btn):
    """Record until red button is pressed or MAX_RECORD_SECS elapses."""
    pa     = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=CHANNELS,
                     rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK)
    frames = []
    start  = time.time()

    set_leds(leds, COLOUR_LISTEN)
    show_oled(oled, "Listening...", "Red=stop")

    while time.time() - start < MAX_RECORD_SECS:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        if red_btn.is_button_pressed():
            break

    stream.stop_stream()
    stream.close()
    pa.terminate()

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)           # paInt16 = 2 bytes per sample
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(frames))
    return tmp.name


def transcribe(whisper_model, audio_path, leds, oled):
    set_leds(leds, COLOUR_THINK)
    show_oled(oled, "Transcribing...")
    segments, _ = whisper_model.transcribe(audio_path, language="en")
    text = " ".join(seg.text.strip() for seg in segments)
    os.unlink(audio_path)
    return text.strip()


def ask_gemini(chat, user_text, leds, oled):
    set_leds(leds, COLOUR_THINK)
    show_oled(oled, "Thinking...", user_text[:32])
    response = chat.send_message(user_text)
    return response.text.strip()



def speak(text, leds, oled):
    set_leds(leds, COLOUR_SPEAK)
    show_oled(oled, text[:32], text[32:64] if len(text) > 32 else "")
    subprocess.run(["espeak-ng", "-s", "145", "-v", "en-us+f3", text],
                   check=False)


def main():
    print("Initialising hardware...")
    green_btn, red_btn, leds, oled = init_hardware()

    print(f"Loading Whisper '{WHISPER_MODEL}' model (first run downloads it)...")
    whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    chat   = client.chats.create(model=GEMINI_MODEL,
                                 config={"system_instruction": SYSTEM_PROMPT})

    set_leds(leds, COLOUR_IDLE)
    show_oled(oled, "AI Assistant", "Press GREEN")
    print("Ready. Press the green button to speak.")

    try:
        while True:
            if green_btn.is_button_pressed():
                pulse_leds(leds, COLOUR_LISTEN, times=2)

                audio_path = record_audio(leds, oled, red_btn)
                user_text  = transcribe(whisper_model, audio_path, leds, oled)

                if not user_text:
                    show_oled(oled, "Didn't hear you", "Try again")
                    set_leds(leds, COLOUR_ERROR)
                    time.sleep(2)
                else:
                    print(f"You: {user_text}")
                    reply = ask_gemini(chat, user_text, leds, oled)
                    print(f"Gemini: {reply}")
                    speak(reply, leds, oled)
                    time.sleep(0.5)

                set_leds(leds, COLOUR_IDLE)
                show_oled(oled, "AI Assistant", "Press GREEN")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nBye!")
        set_leds(leds, COLOUR_OFF)
        oled.clear()
        oled.display()


if __name__ == "__main__":
    main()
