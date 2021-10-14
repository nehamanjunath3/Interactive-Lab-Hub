from vosk import Model, KaldiRecognizer
import sys
import os
import wave
import json
import gtts
import os
import sys

def playsound(text):
    print(text)
    tts = gtts.gTTS(text, lang="en")
    tts.save("speak.mp3")
    os.system("mplayer -ao alsa -really-quiet -noconsolecontrols speak.mp3")


if not os.path.exists("model"):
    print ("Please download the model from https://github.com/alphacep/vosk-api/blob/master/doc/models.md and unpack as 'model' in the current folder.")
    exit (1)

wf = wave.open(sys.argv[1], "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print ("Audio file must be WAV format mono PCM.")
    exit (1)

model = Model("model")
# Large vocabulary free form recognition
rec = KaldiRecognizer(model, wf.getframerate(), '["oh one two three four five six seven eight nine zero date party winter", "[unk]"]')
final_text = ""

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        res = json.loads(rec.Result())
        # print(res)
        # print(res['text'])
        final_text += res['text']

occasion = final_text.split()
print (occasion)
