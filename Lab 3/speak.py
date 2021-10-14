import gtts
import os
import sys

text = sys.argv[1]
tts = gtts.gTTS(text, lang="en")
tts.save("speak.mp3")
os.system("mplayer -ao alsa -really-quiet -noconsolecontrols speak.mp3")
