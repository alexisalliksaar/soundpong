from queue import Queue
from threading import Thread

import librosa
import numpy as np
import pyaudio


#Sain siit päris palju abi, kuidas kinni püüda mikrofoni sisendit:
# https://www.youtube.com/watch?v=2kSPbH4jWME
messages = Queue()
recordings = Queue()


FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100
CHUNK = 4096

device_id = 1


def start_recording(queue, record_seconds=0, configured_min=0, configured_max=0, mic_id=1):
    messages.queue.clear()
    recordings.queue.clear()
    queue.queue.clear()

    messages.put(True)

    record = Thread(target=lambda: record_microphone(record_seconds, mic_id))
    record.start()

    resolve = Thread(target=lambda: resolver(queue, record_seconds, configured_min, configured_max))
    resolve.start()

    pass


def stop_recording():
    messages.get()
    recordings.put(-1)


def record_microphone(record_seconds, mic_id):
    p_aud = pyaudio.PyAudio()
    stream = p_aud.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=mic_id,
                        frames_per_buffer=CHUNK)
    frames = []
    while not messages.empty():
        data = stream.read(CHUNK)
        if record_seconds == 0:
            recordings.put(data)
        else:
            if len(frames) >= (RATE * record_seconds) / CHUNK:
                recordings.put(frames.copy())
                break
            else:
                frames.append(data)

    stream.stop_stream()
    stream.close()
    p_aud.terminate()
    return


# This is the average human speech frequencies with some padding
MIN_FREQUENCY = 70
MAX_FREQUENCY = 300


def resolver(queue, record_seconds, configured_min=0, configured_max=0):
    try:
        if record_seconds != 0:
            while not messages.empty():
                # töötleme andmed numpyarrayks, mis on meile sobiva kujuga
                data = recordings.get()
                if data == -1:
                    return
                sound_arrays = []
                for row in data:
                    s_arr = np.frombuffer(row, dtype=np.float32)
                    sound_arrays.append(s_arr)
                data = sound_arrays[0]
                for j in range(1, len(sound_arrays)):
                    data = np.concatenate((data, sound_arrays[j]), axis=0)
                #leiame kõikide andmete peale keskmise hääle kõrguse
                result_frequency = pitch_resolver(data, MIN_FREQUENCY, MAX_FREQUENCY)
                queue.put(result_frequency)
        else:
            while not messages.empty():
                data = recordings.get()
                if data == -1:
                    return
                #töötleme andmed numpyarrayks
                sound_array = np.frombuffer(data, dtype=np.float32)
                #leiame keskmise kõrguse
                result_frequency = pitch_resolver(sound_array, configured_min, configured_max)
                print(result_frequency)
                queue.put(result_frequency)
    except:
        queue.put(-2)


def pitch_resolver(data, fmin, fmax):
    #kasutan librosat, et leida audio 'fundamental frequency', ehk hääle baaskõrgus
    #samuti ütleb librosa kas mingis ajaühikus oli kõne või mitte
    f0, voiced_flag, voiced_prob = librosa.pyin(y=data, sr=RATE, fmin=fmin, fmax=fmax, frame_length=CHUNK)
    result_frequencies = []
    for j in range(len(f0)):
        #oli kõne sel hetkel, seega lisame ta listi
        if voiced_flag[j]:
            result_frequencies.append(f0[j])
    if len(result_frequencies) == 0:
        return -1
    else:
        return sum(result_frequencies) / len(result_frequencies)


#print("recording")
#result_queue = Queue()
#start_recording(result_queue, configured_min=100, configured_max=200)
#try:
#    while not messages.empty():
#        result = result_queue.get()
#except KeyboardInterrupt:
#    stop_recording()


def configure_device():
    # Kuidas saada mikrofonide nimekiri
    # https://stackoverflow.com/questions/36894315/how-to-select-a-specific-input-device-with-pyaudio
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    valid_ids = []
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            valid_ids.append(i)
            print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

    p.terminate()
    while True:
        deviceid = int(input("Please input the id of your microphone: "))
        if deviceid in valid_ids:
            break
        else:
            print("Invalid input, please try again")
    return deviceid

if __name__ == '__main__':
    configure_device()