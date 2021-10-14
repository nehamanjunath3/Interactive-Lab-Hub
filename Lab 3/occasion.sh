say() { local IFS=+;/usr/bin/mplayer -ao alsa -really-quiet -noconsolecontrols "http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q=$*&tl=en"; }
#say $*
say " Hi Neha! I'm Climaide! Your personal style assistant. What occasion would you like to dress for?"

#arecord -f cd -r 16000 -d 5 -t wav recorded.wav && sox recorded.wav recorded_mono.wav remix 1,2

arecord -D hw:2,0 -f cd -c1 -r 48000 -d 5 -t wav recorded_mono.wav
python3 word_list.py recorded_mono.wav

#say " Press the button to get styling ideas"
#say "Its winter. So dont forget your coat"
#python3 speak.py " Hi Neha! I'm Climaide! Your personal style assistant. What occasion would you like to dress for?"
#arecord -D hw:3,0 -f cd -c1 -r 48000 -d 5 -t wav recorded_mono.wav
#python3 climaide.py recorded_mono.wav
