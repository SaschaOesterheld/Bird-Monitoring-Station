"""
Microphone recording service for the Bird Monitor system.

This module continuously records audio from the first available sound device found,
splits the recording into fixed-duration WAV files, and stores them in
a configured output directory for later processing by the BirdNET
classification pipeline.

The recording loop is intended to run in a dedicated background thread
while other components process previously recorded audio files.
"""

import sounddevice as sd
import wave
import os
import time
from datetime import datetime

class Microphone_Server:
	"""
    Continuously record audio from a microphone.

    The class automatically detects an available input device,
    records fixed-length audio segments, and stores them as WAV
    files in the configured output directory.
    """
	def __init__(self,audio_file_dir,sample_rate_manual,file_length=6):
			"""
			Initialize the microphone recording service.

			Configures the recording device, sampling parameters, and output
			directory.

			Args:
				audio_file_dir: Directory where recordings are stored.
				sample_rate_manual: Fallback sample rate if the default fails.
				file_length: Duration of each recording in seconds.
			"""
			print("Microphone Server Init...")
			print(sd.query_devices())

			# ===== Configuration =====
			# How many seconds each recorded file should be
			self.file_length = file_length

			# Where to save
			self.OUTPUT_FOLDER = audio_file_dir
			# =========================

			# Create output folder if it doesn't exist
			os.makedirs(self.OUTPUT_FOLDER, exist_ok=True)
			self.exists = True
			#try out first device id that is an Input device, use manual device id if none found
			try:
				sd.default.device = self.find_input_device()
			except Exception as e:
				print("Error: No Input Device was found for the Microphone!")
				print(e)
				self.exists = False
			print(f"Using Device with ID {sd.default.device}:")
			info = sd.query_devices(sd.default.device, "input")
			print(info)
			# Sampling settings
			self.SAMPLE_RATE = int(info["default_samplerate"])
			self.FALLBACK_SAMPLE_RATE = sample_rate_manual
			self.CHANNELS = 1          # 1 = mono, 2 = stereo
			self.fallback_triggered=False

	def find_input_device(self):
		"""
		Locate the first available audio input device.

		Returns:
			The index of the selected input device.

		Raises:
			RuntimeError: If no input device is available.
		"""
		print("Finding Input Devices...")
		devices = sd.query_devices()
		input_devices = []

		for idx, dev in enumerate(devices):
			if dev["max_input_channels"] > 0:
				input_devices.append((idx, dev))

		if len(input_devices) == 0:
			raise RuntimeError("No input devices found")

		if len(input_devices) > 1:
			print("Multiple input devices found:")
			for idx, dev in input_devices:
				print(idx, dev["name"])

		# Return the first (or only) input device
		return input_devices[0][0]

	def record_segment(self, duration):
		"""
		Record a single audio segment.

		Args:
			duration: Recording duration in seconds.

		Returns:
			Raw audio data encoded as 16-bit PCM bytes.
		"""
		print(f"Recording for {duration} seconds...")

		recording = []

		def callback(indata, frames, time, status):
			if status:
				print(status)
			recording.append(indata.copy())

		with sd.InputStream(
			samplerate=self.SAMPLE_RATE,
			channels=self.CHANNELS,
			dtype="int16",
			callback=callback
		):
			sd.sleep(int(duration * 1000))

		return b"".join(chunk.tobytes() for chunk in recording)

	def save_wav(self, data, filename):
		"""
		Save raw PCM audio data as a WAV file.

		Args:
			data: Raw audio bytes.
			filename: Destination WAV file path.
		"""
		with wave.open(filename, "wb") as wf:
			wf.setnchannels(self.CHANNELS)
			wf.setsampwidth(2)
			wf.setframerate(self.SAMPLE_RATE)
			wf.writeframes(data)
		print(f"Saved {filename}",flush=True)

	def mainloop(self):
		"""
		Continuously record and save audio segments.

		The method repeatedly records fixed-length audio clips and stores
		them as timestamped WAV files until the application is terminated.
		If recording fails, a fallback sample rate is attempted once.
		"""
		print("Started MicrophoneServer!")
		if not self.exists:
			return
		try:
			while True:
				# Generate a timestamped filename
				timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
				out_path = os.path.join(self.OUTPUT_FOLDER, f"recording_{timestamp}.wav")
				# Record audio
				audio_data = self.record_segment(self.file_length)
				# Save to WAV
				self.save_wav(audio_data, out_path)
				# Small sleep to avoid tight loop (optional)
				time.sleep(0.01)

		except KeyboardInterrupt:
			print("Recording stopped by user.")
		except Exception as e:
			print(e)
			if not self.fallback_triggered:
				print(f"Fell back to manual SampleRate {self.FALLBACK_SAMPLE_RATE}")
				self.fallback_triggered = True
				self.SAMPLE_RATE=self.FALLBACK_SAMPLE_RATE
				self.mainloop()

#ms = microphone_server2("/home/bimo2/Desktop/bimo2_project_files/birdnet-mini/sound_data",2,32000)
#ms.mainloop()
