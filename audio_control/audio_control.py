#!/usr/bin/env python
import audioop
import glob
import io
import numpy as np
import os
import picar
import pyaudio
import requests
import wave
import sys
import tensorflow as tf
import time

from datetime import datetime
from picar import back_wheels, front_wheels
from tensorflow.keras.models import load_model

MODEL_PATH="./speech_command_GRU_refine_self_2.tf.tflite"
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
OUT_RATE = 16000
RECORD_SECONDS = 20
WAVE_OUTPUT_FILENAME = "./test_files/recorded.wav"
DEV_INDEX = 1
CV_STATE=None
interpreter=None
previous_half=None

def num_to_class(num):
  classes = ['backward', 'forward', 'follow_lane', 'fwleft', 'noise', 'fwright', 'stop', 'unknown']
  if num >= 0 and num < len(classes):
    return classes[num]
  else:
    return 'not_found'

def get_spectrogram_for_frame(wave_one):
  zero_padding = tf.zeros([16000] - tf.shape(wave_one), dtype=tf.float32)
  wave_one = tf.cast(wave_one, dtype=tf.float32)
  equal_length = tf.concat([wave_one, zero_padding], 0)
  # Convert the waveform to a spectrogram via a STFT.
  spectrogram = tf.signal.stft(
      equal_length, frame_length=255, frame_step=128)
  # Obtain the magnitude of the STFT.
  spectrogram = tf.abs(spectrogram)
  return spectrogram

def predict_for_spectrogram(interpreter, spectrogram):
    spectrogram = tf.reshape(spectrogram, (-1, spectrogram.shape[-2], spectrogram.shape[-1]))
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    interpreter.set_tensor(input_details[0]["index"], np.array(spectrogram, dtype=np.float32))
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]["index"])
    softmax = tf.nn.softmax(output[0])
    max_score = tf.math.reduce_max(softmax)

    cls = num_to_class(tf.argmax(output, axis=1).numpy()[0])
    return (cls, max_score.numpy())

def save_wav_file(waves, filename):
  wf = wave.open(filename, 'wb')
  wf.setnchannels(CHANNELS)
  wf.setsampwidth(2)
  wf.setframerate(OUT_RATE)
  wf.writeframes(waves)
  wf.close()

def run_action(action):
  params = {'action': action}
  r = requests.get('http://127.0.0.1:8000/run', params=params)

def callback(in_data, frame_count, time_info, flag):
  global CV_STATE, previous_half, interpreter
  newdata, CV_STATE = audioop.ratecv(in_data, 2, 1, RATE, OUT_RATE, CV_STATE)
  if previous_half is not None:
      temp_file = io.BytesIO()
      save_wav_file(b''.join([previous_half, newdata]), temp_file)
      temp_file.seek(0)
      audio, _ = tf.audio.decode_wav(contents=temp_file.read())
      audio = tf.squeeze(audio, axis=-1)
      spectrogram = get_spectrogram_for_frame(audio)
      cls, max_score = predict_for_spectrogram(interpreter, spectrogram)
      if max_score > 0.90 and cls not in ['noise', 'unknown']:
        print(cls, max_score)
        if cls in ['forward', 'backward', 'stop']:
            run_action('fwstraight')
        run_action(cls)
        print('action done')
      #timestr = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S.%f')[:-3]
      #fname = 'in-%s-%s.wav' % (timestr, cls)
      #save_wav_file(b''.join([previous_half, newdata]), os.path.join('./test_files', fname))
  previous_half = newdata
  return (in_data, pyaudio.paContinue)

def audio_control():
  p = pyaudio.PyAudio()

  stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
          input_device_index = DEV_INDEX,
          input=True, frames_per_buffer=int(RATE/2), # half second
          stream_callback=callback)

  print('Starting audio control')
  try:
      stream.start_stream()
      while stream.is_active():
          time.sleep(10)
  except KeyboardInterrupt:
      stream.stop_stream()
      stream.close()
      p.terminate()

def predict_for_file(filepath):
  # Load audio from file
  audio_binary = tf.io.read_file(filepath)
  audio, _ = tf.audio.decode_wav(contents=audio_binary)
  waveform = tf.squeeze(audio, axis=-1)

  # Get spectrogram
  spectrograms = []
  waves = []
  frame_len = OUT_RATE  # 1 second length
  frame_step = int(frame_len // 2)  # half second step
  total_length = tf.shape(waveform)[0]
  num_frames = total_length//frame_step
  if total_length > num_frames * frame_step:
    num_frames += 1

  for i in range(num_frames):
    wave_one = waveform[i * frame_step: i * frame_step + frame_len]
    waves.append(wave_one)
    spectrogram = get_spectrogram_for_frame(wave_one)
    spectrograms.append(spectrogram)
  
  # get predictions
  preds = []
  for i in range(len(spectrograms)):
    pred = predict_for_spectrogram(interpreter, spectrograms[i])
    if pred is not None:
        preds.append(pred)

    #save_wav_file(waves[i], os.path.join('./test_files', 'splitted_%s_%d.wav' % (cls, i)))

    #tflite_interpreter.reset_all_variables()
  print(preds)
  return preds

def record_to_wav():
  p = pyaudio.PyAudio()

  # Uncomment below codes for the first time to check index number for your device
  print(p.get_device_count())
  for ii in range(p.get_device_count()):
    print(p.get_device_info_by_index(ii)['name'])

  stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
          input_device_index = DEV_INDEX,
          input=True, frames_per_buffer=CHUNK)

  print("* recording")

  frames = []

  cvstate = None
  for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    newdata, cvstate = audioop.ratecv(data, p.get_sample_size(FORMAT), 1, RATE, OUT_RATE, cvstate)
    frames.append(newdata)

  print("* done recording")

  stream.stop_stream()
  stream.close()
  p.terminate()

  save_wav_file(b''.join(frames), WAVE_OUTPUT_FILENAME)

def main():
  global interpreter
  interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
  interpreter.allocate_tensors()

  #audio_control()
  #predict_for_file('./test_files/recorded.wav')
  record_to_wav()

if __name__ == "__main__":
    main()
