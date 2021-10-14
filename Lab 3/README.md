# Chatterboxes
[![Watch the video](https://user-images.githubusercontent.com/1128669/135009222-111fe522-e6ba-46ad-b6dc-d1633d21129c.png)](https://www.youtube.com/embed/Q8FWzLMobx0?start=19)

In this lab, we want you to design interaction with a speech-enabled device--something that listens and talks to you. This device can do anything *but* control lights (since we already did that in Lab 1).  First, we want you first to storyboard what you imagine the conversational interaction to be like. Then, you will use wizarding techniques to elicit examples of what people might say, ask, or respond.  We then want you to use the examples collected from at least two other people to inform the redesign of the device.

We will focus on **audio** as the main modality for interaction to start; these general techniques can be extended to **video**, **haptics** or other interactive mechanisms in the second part of the Lab.

## Prep for Part 1: Get the Latest Content and Pick up Additional Parts 

### Pick up Additional Parts

As mentioned during the class, we ordered additional mini microphone for Lab 3. Also, a new part that has finally arrived is encoder! Please remember to pick them up from the TA.

### Get the Latest Content

As always, pull updates from the class Interactive-Lab-Hub to both your Pi and your own GitHub repo. As we discussed in the class, there are 2 ways you can do so:

**\[recommended\]**Option 1: On the Pi, `cd` to your `Interactive-Lab-Hub`, pull the updates from upstream (class lab-hub) and push the updates back to your own GitHub repo. You will need the *personal access token* for this.

```
pi@ixe00:~$ cd Interactive-Lab-Hub
pi@ixe00:~/Interactive-Lab-Hub $ git pull upstream Fall2021
pi@ixe00:~/Interactive-Lab-Hub $ git add .
pi@ixe00:~/Interactive-Lab-Hub $ git commit -m "get lab3 updates"
pi@ixe00:~/Interactive-Lab-Hub $ git push
```

Option 2: On your your own GitHub repo, [create pull request](https://github.com/FAR-Lab/Developing-and-Designing-Interactive-Devices/blob/2021Fall/readings/Submitting%20Labs.md) to get updates from the class Interactive-Lab-Hub. After you have latest updates online, go on your Pi, `cd` to your `Interactive-Lab-Hub` and use `git pull` to get updates from your own GitHub repo.

## Part 1.
### Text to Speech 

In this part of lab, we are going to start peeking into the world of audio on your Pi! 

We will be using a USB microphone, and the speaker on your webcamera. (Originally we intended to use the microphone on the web camera, but it does not seem to work on Linux.) In the home directory of your Pi, there is a folder called `text2speech` containing several shell scripts. `cd` to the folder and list out all the files by `ls`:

```
pi@ixe00:~/text2speech $ ls
Download        festival_demo.sh  GoogleTTS_demo.sh  pico2text_demo.sh
espeak_demo.sh  flite_demo.sh     lookdave.wav
```

You can run these shell files by typing `./filename`, for example, typing `./espeak_demo.sh` and see what happens. Take some time to look at each script and see how it works. You can see a script by typing `cat filename`. For instance:

```
pi@ixe00:~/text2speech $ cat festival_demo.sh 
#from: https://elinux.org/RPi_Text_to_Speech_(Speech_Synthesis)#Festival_Text_to_Speech

echo "Just what do you think you're doing, Dave?" | festival --tts
```

Now, you might wonder what exactly is a `.sh` file? Typically, a `.sh` file is a shell script which you can execute in a terminal. The example files we offer here are for you to figure out the ways to play with audio on your Pi!

You can also play audio files directly with `aplay filename`. Try typing `aplay lookdave.wav`.

\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*
(This shell file should be saved to your own repo for this lab.)

Bonus: If this topic is very exciting to you, you can try out this new TTS system we recently learned about: https://github.com/rhasspy/larynx

### Speech to Text

Now examine the `speech2text` folder. We are using a speech recognition engine, [Vosk](https://alphacephei.com/vosk/), which is made by researchers at Carnegie Mellon University. Vosk is amazing because it is an offline speech recognition engine; that is, all the processing for the speech recognition is happening onboard the Raspberry Pi. 

In particular, look at `test_words.py` and make sure you understand how the vocab is defined. Then try `./vosk_demo_mic.sh`

One thing you might need to pay attention to is the audio input setting of Pi. Since you are plugging the USB cable of your webcam to your Pi at the same time to act as speaker, the default input might be set to the webcam microphone, which will not be working for recording.

\*\***Write your own shell file that verbally asks for a numerical based input (such as a phone number, zipcode, number of pets, etc) and records the answer the respondent provides.**\*\*


https://user-images.githubusercontent.com/64258179/135953553-e7c626b8-c291-449e-9603-ffc8fcc6028c.mp4


Bonus Activity:

If you are really excited about Speech to Text, you can try out [Mozilla DeepSpeech](https://github.com/mozilla/DeepSpeech) and [voice2json](http://voice2json.org/install.html)
There is an included [dspeech](./dspeech) demo  on the Pi. If you're interested in trying it out, we suggest you create a seperarate virutal environment for it . Create a new Python virtual environment by typing the following commands.

```
pi@ixe00:~ $ virtualenv dspeechexercise
pi@ixe00:~ $ source dspeechexercise/bin/activate
(dspeechexercise) pi@ixe00:~ $ 
```

### Serving Pages

In Lab 1, we served a webpage with flask. In this lab, you may find it useful to serve a webpage for the controller on a remote device. Here is a simple example of a webserver.

```
pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ python server.py
 * Serving Flask app "server" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 162-573-883
```
From a remote browser on the same network, check to make sure your webserver is working by going to `http://<YourPiIPAddress>:5000`. You should be able to see "Hello World" on the webpage.

### Storyboard

Storyboard and/or use a Verplank diagram to design a speech-enabled device. (Stuck? Make a device that talks for dogs. If that is too stupid, find an application that is better than that.) 

\*\***Post your storyboard and diagram here.**\*\*

![WhatsApp Image 2021-10-04 at 11 01 26 PM](https://user-images.githubusercontent.com/64258179/135953626-3054f4ae-3396-4ca7-97f7-ebd4b913d735.jpeg)

Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses. 

\*\***Please describe and document your process.**\*\*

This idea was inspired by New York and its erratic weather. While there are so many activities to do in the city, we also need to aware of the weather changes and dress accordingly. This device Climaide gives the user style advice keeping the weather in mind.
__Dialogue__
User: Hey buddy
Climaide: Hey User
User: I'm going on a date tonight. What do I wear?
Climaide: Wear a dress. Along with that carry a coat. The temperature is going to be 20 degree celcius
USer: Thank you! Is it going to rain?
Climaide: There's 20% chance of precipitation
User: Thank you climaide


### Acting out the dialogue!

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing.  Please record this interaction (for example, using Zoom's record feature).

\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*

The dialogue was more complex than expected. Users generally tend to get too personal nd ask too many options when it come to styling. Also the occasion on which the style advice should be given needs to be more detailed as there multiple options for each occasion. 


### Wizarding with the Pi (optional)
In the [demo directory](./demo), you will find an example Wizard of Oz project. In that project, you can see how audio and sensor data is streamed from the Pi to a wizard controller that runs in the browser.  You may use this demo code as a template. By running the `app.py` script, you can see how audio and sensor data (Adafruit MPU-6050 6-DoF Accel and Gyro Sensor) is streamed from the Pi to a wizard controller that runs in the browser `http://<YouPiIPAddress>:5000`. You can control what the system says from the controller as well!

\*\***Describe if the dialogue seemed different than what you imagined, or when acted out, when it was wizarded, and how.**\*\*

The dialogue was significantly different from when it was imagined and from when it was acted out and wizared. When it was acted out I realised the dialogue needs to be more nuanced with a lot ore options. Duriing the wizarding process, the dialogue from the system could be monitored and also inspiration was drawn to use other sensors to make the interaction more engaging

# Lab 3 Part 2

For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.

## Prep for Part 2

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings...
The users usually say multiple words for different occasions. So an extensive library including all the possible words would be more effective. Also users dont speak partial sentences or just key words. So using structured sentences as input wouln't work. So extracting keywords is more effective.
2. What are other modes of interaction _beyond speech_ that you might also use to clarify how to interact?
One of the most common feedbacks involved having images as a way of communicating rather than just given the problem statement. So i decided on including the tft display to show different styling options for the user.
3. Make a new storyboard, diagram and/or script based on these reflections.
![WhatsApp Image 2021-10-13 at 10 09 46 PM](https://user-images.githubusercontent.com/64258179/137238840-98f7eb64-5d47-4c29-8ec7-f4fb86fe8f3b.jpeg)

## Prototype your system

The system includes:
* Raspberry Pi 
* Qwiic Red Button
* Participants interact with the system 

*Document how the system works*
The device asks the user to input the occasion they are dressing for. Based on the user's input the device gives a suggestion on what would be good way to dress. All these responses from the device are stored in separate shell files. The user's input is recored from the microphone and specific words are chosen to determine the different cases. If the users words aren't in the vocabulary of the device then it returns a didn't understand message. For more options. The user is asked to press the red qwiic button to see different styling options for different occasions.

*Include videos or screencaptures of both the system and the controller.*


https://user-images.githubusercontent.com/64258179/137237187-fdb75142-b7a7-4693-afa5-4e7e60f87a12.mp4


## Test the system
Try to get at least two people to interact with your system. (Ideally, you would inform them that there is a wizard _after_ the interaction, but we recognize that can be hard.)

Answer the following:

### What worked well about the system and what didn't?
\*\**The partcipants really liked the idea and were impressed with the images and the speech responses. But they asked for more scenarios which the device wasn't prepared to handle. The timing and the delay in response was also a painpoint according to the users. They also felt that the stying options displayed on the screen should be an autonomous feature. They felt more control could be given to the user in choosing the dress options displayed on the screen. *\*\*

### What worked well about the controller and what didn't?

\*\**The red button was useful but a rotary encoder or joystick in picking the dresses would have felt more engaging.*\*\*

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?

\*\**The design has to prepaperd for all the edge case scenarios especially while recording the responses from the user which the device was not prepared for.*\*\*


### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?

\*\**Touch sensors and gesture control could be used for better interactions. Also temeprature sensor could be used to sense the temeprature of the room and suggest clothing based on that.*\*\*

