# SoundPong

Recreation of the classic pong game, but the player uses the pitch of their voice to control the up and down movement of the player rectangle.

## How to run the game
* Install Python
* Use pip to download packages: [pygame](https://pypi.org/project/pygame/), [PyAudio](https://pypi.org/project/PyAudio/), [numpy](https://pypi.org/project/numpy/), [librosa](https://pypi.org/project/librosa/)
* Configure the [SoundPong.conf file](SoundPong.conf):
  * min_frequency and max_frequency - the maximum and minimum frequency for your voice (in Hz) that you want to use. For reference male speaking voice is usually in the range 85 Hz - 180 Hz and female speaking voice is usually in the range 165 Hz - 255 Hz.
  * device_id - the id of your microphone. If you run the main function in [sound_resolver.py](sound_resolver.py), the id-s and names of the detected microphones are displayed.
  * ai_difficulty - value can be either 'EASY', 'MEDIUM' or 'HARD'.
* Run the main function in [main.py](main.py)
