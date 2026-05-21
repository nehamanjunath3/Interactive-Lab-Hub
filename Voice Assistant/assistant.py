#!/usr/bin/env python3
"""
Voice AI Assistant for Raspberry Pi
- Green Qwiic button (addr 0x5F): press to talk  [optional]
- Red Qwiic button  (addr 0x6F): stop recording  [optional]
- Qwiic LED stick                : status colors  [optional]
- faster-whisper                 : speech-to-text (runs locally)
- Gemini API                     : AI responses
- espeak-ng                      : text-to-speech

Falls back to keyboard (Enter to start/stop) when hardware not connected.
"""

import os
import time
import wave
import tempfile
import subprocess

import pyaudio
import anthropic
from faster_whisper import WhisperModel

# ── Config ────────────────────────────────────────────────────────────────────
SAMPLE_RATE     = 44100
CHANNELS        = 1
CHUNK           = 1024
MAX_RECORD_SECS = 5
WHISPER_MODEL   = "tiny"
CLAUDE_MODEL    = "claude-haiku-4-5-20251001"
SYSTEM_PROMPT   = (
    "You are a friendly voice assistant running on a Raspberry Pi. "
    "Keep every response under 2 sentences so it fits on a small screen "
    "and doesn't take long to read aloud."
)

COLOUR_OFF    = (  0,   0,   0)
COLOUR_IDLE   = (  5,   5,   5)
COLOUR_LISTEN = (  0,  50, 255)
COLOUR_THINK  = (128,   0, 255)
COLOUR_SPEAK  = (  0, 200,  50)
COLOUR_ERROR  = (255,  30,   0)


def try_import_qwiic():
    """Return (green_btn, red_btn, leds) or Nones if hardware not available."""
    try:
        import qwiic_button
        import qwiic_led_stick
        green = qwiic_button.QwiicButton(address=0x5F)
        red   = qwiic_button.QwiicButton(address=0x6F)
        leds  = qwiic_led_stick.QwiicLEDStick()
        # Quick connectivity check
        green_ok = green.is_connected()
        red_ok   = red.is_connected()
        leds_ok  = leds.is_connected()
        if not green_ok: print("[WARN] green button not found")
        if not red_ok:   print("[WARN] red button not found")
        if not leds_ok:  print("[WARN] LED stick not found")
        return (
            green if green_ok else None,
            red   if red_ok   else None,
            leds  if leds_ok  else None,
        )
    except Exception as e:
        print(f"[WARN] Qwiic hardware unavailable: {e}")
        return None, None, None


def set_leds(leds, colour):
    if leds is None:
        return
    try:
        r, g, b = colour
        leds.set_all_LED_color(r, g, b)
    except Exception:
        pass


def pulse_leds(leds, colour, times=2):
    for _ in range(times):
        set_leds(leds, colour)
        time.sleep(0.12)
        set_leds(leds, COLOUR_OFF)
        time.sleep(0.12)


def btn_pressed(btn):
    if btn is None:
        return False
    try:
        return btn.is_button_pressed()
    except Exception:
        return False


def find_input_device(pa):
    """Return index of first USB input device, or None for default."""
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0 and "USB" in info["name"]:
            print(f"  Using mic: {info['name']} (index {i})")
            return i
    return None


def record_audio(leds, red_btn, keyboard_mode):
    pa          = pyaudio.PyAudio()
    input_index = find_input_device(pa)
    stream      = pa.open(format=pyaudio.paInt16, channels=CHANNELS,
                          rate=SAMPLE_RATE, input=True,
                          input_device_index=input_index,
                          frames_per_buffer=CHUNK)
    frames = []
    start  = time.time()
    set_leds(leds, COLOUR_LISTEN)

    if keyboard_mode:
        print(f"  Recording for {MAX_RECORD_SECS}s... speak now!")
        while time.time() - start < MAX_RECORD_SECS:
            frames.append(stream.read(CHUNK, exception_on_overflow=False))
    else:
        print("  Recording... press red button to stop")
        while not btn_pressed(red_btn) and time.time() - start < MAX_RECORD_SECS:
            frames.append(stream.read(CHUNK, exception_on_overflow=False))

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


def transcribe(whisper_model, audio_path, leds):
    set_leds(leds, COLOUR_THINK)
    print("  Transcribing...")
    segments, _ = whisper_model.transcribe(audio_path, language="en")
    text = " ".join(seg.text.strip() for seg in segments)
    os.unlink(audio_path)
    return text.strip()


def ask_claude(client, history, user_text, leds):
    set_leds(leds, COLOUR_THINK)
    print("  Thinking...")
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


def speak(text, leds):
    set_leds(leds, COLOUR_SPEAK)
    print(f"  Claude: {text}")
    subprocess.run(["espeak-ng", "-s", "145", "-v", "en-us+f3", text], check=False)


def main():
    print("Initialising hardware...")
    green_btn, red_btn, leds = try_import_qwiic()
    keyboard_mode = green_btn is None
    if keyboard_mode:
        print("[INFO] No buttons detected — using keyboard (Enter to talk)")

    print(f"Loading Whisper '{WHISPER_MODEL}' model...")
    whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

    client  = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    history = []

    set_leds(leds, COLOUR_IDLE)
    prompt = "Press Enter to speak" if keyboard_mode else "Press GREEN button to speak"
    print(f"\nReady! {prompt}. Ctrl+C to quit.\n")

    try:
        while True:
            if keyboard_mode:
                input("[ Press Enter to speak ]")
                triggered = True
            else:
                triggered = btn_pressed(green_btn)

            if triggered:
                pulse_leds(leds, COLOUR_LISTEN)
                audio_path = record_audio(leds, red_btn, keyboard_mode)
                user_text  = transcribe(whisper_model, audio_path, leds)

                if not user_text:
                    print("  Didn't catch that — try again")
                    set_leds(leds, COLOUR_ERROR)
                    time.sleep(1)
                else:
                    print(f"  You: {user_text}")
                    reply = ask_claude(client, history, user_text, leds)
                    speak(reply, leds)
                    time.sleep(0.5)

                set_leds(leds, COLOUR_IDLE)

            if not keyboard_mode:
                time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nBye!")
        set_leds(leds, COLOUR_OFF)


if __name__ == "__main__":
    main()
