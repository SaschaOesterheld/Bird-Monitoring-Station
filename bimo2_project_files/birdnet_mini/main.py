"""
 This is the Main application for the BiMo2 system.

This module coordinates the operation of BiMo2 by 
(1) initializing hardware components,
(2) loading the BirdNET machine learning model,
(3) continuously processing recorded audio to identify bird species an finally
(4) sending the generated data to a website.

Responsibilities:
- Initialize the LCD Handler, and Microphone Server
- Load the BirdNET TensorFlow Lite model and label file with bird names
- Monitor the recording directory for new audio files
- Resample and split audio recordings into inference-ready chunks
- Run bird species classification on each audio segment
- send the most recently detected bird and weather to the LCD Handler
- send weather measurements and bird detections to the website
- Manage temporary audio files and perform directory housekeeping

The application is intended to run continuously on a Raspberry Pi and uses
background threads for the LCD interface and audio recording while the main
thread performs audio processing and bird classification. Weather data is
read before the sending of data to the website.

Author - Sascha Oesterheld
05.08.2026
"""

#################### Libraries ####################
import os
import audio
import model
from weather_i2c import WeatherSensor
import shutil
import time
import csv
import lcddriver
from datetime import datetime as dt
import logging
import threading
import microphone_server
from pathlib import Path
import librosa
import numpy as np

#Functions Website
from database import init_db, insert_temperature, insert_bird_detection

#################### Variables  ###################
# Debug logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Microphone
mic_device_id = -1
sample_rate=16000
################### Directories ###################
# Get Project path
BASE_DIR = Path(__file__).resolve().parent.parent
# Set the name of the logs folder
LOGGING_DIR_NAME = "logs"
# Directory where audio files are saved
audio_dir = BASE_DIR / "birdnet-mini/sound_data/"
csv_dir = BASE_DIR / "birdnet-mini/csv_data/"
# Files needed for the model that detects the birds
label_file = BASE_DIR / "models/BirdNET_GLOBAL_6K_V2.4_Labels.txt"
model_file = BASE_DIR / "models/BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite"
# Set the Log Filepath
log_dir = BASE_DIR / LOGGING_DIR_NAME
log_file = log_dir / f"{Path(__file__).stem}.log"
os.makedirs(log_dir, exist_ok=True)
logger.addHandler(logging.FileHandler(log_file))
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")

# Ensure directories exist
os.makedirs(audio_dir, exist_ok=True)
os.makedirs(csv_dir, exist_ok=True)

#################### Functions ####################
def adjust_string(input_string):
    """
    Format a string for the LCD display.

    Strings longer than 20 characters are truncated.
    Shorter strings are padded with spaces so that the
    returned string is exactly 20 characters long.

    Args:
        input_string: Input text.

    Returns:
        A 20-character string suitable for LCD output.
    """
    # If the string is longer than 20 characters, slice it
    if len(input_string) > 20:
        return input_string[:20]
    # If the string is shorter, pad it with spaces
    else:
        return input_string.ljust(20)


def remove_spaces_commas(input_string):
    """
    Remove spaces and commas from a string.

    Args:
        input_string: String to clean.

    Returns:
        The cleaned string.
    """
    return input_string.replace(" ", "").replace(",", "")


def get_csv_filename():
    """Generate a CSV filename based on the current date."""
    cur_date = dt.now().strftime('%Y-%m-%d')  # YYYY-MM-DD format
    return os.path.join(csv_dir, f"ai_results_{cur_date}.csv")


def write_to_csv(data):
    """Append data to the daily CSV file."""
    csv_file = get_csv_filename()
    file_exists = os.path.isfile(csv_file)

    # Open CSV file in append mode
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Write header only if the file is new
        if not file_exists:
            writer.writerow(["Date", "Time", "AI Output", "Weather"])

        # Write the data row
        writer.writerow(data)
    
def to_48k(samples, sr=sample_rate):
    """
    Resample an audio signal to 48 kHz.

    Args:
        samples: Audio samples.
        sr: Original sampling rate.

    Returns:
        Audio samples resampled to 48 kHz as float32.
    """
    if len(samples) % 48000 == 0:
        return samples.astype(np.float32)
    return librosa.resample(
        samples.astype(np.float32),
        orig_sr=16000,
        target_sr=48000)

def fix_length(x, target_len=144000):
    """
    Pad or trim an audio signal to a fixed length.

    Args:
        x: Audio samples.
        target_len: Desired number of samples.

    Returns:
        Audio array with exactly ``target_len`` samples.
    """
    if len(x) > target_len:
        return x[:target_len]
    elif len(x) < target_len:
        return np.pad(x, (0, target_len - len(x)))
    return x
    
def prune_wav_files(directory=audio_dir, max_files=40):
    """
    Delete the oldest WAV files once the directory exceeds
    the configured maximum number of recordings.

    Args:
        directory: Directory containing WAV files.
        max_files: Maximum number of WAV files to keep.

    Returns:
        Number of deleted files.
    """
    # Get full paths to .wav files
    wav_files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith(".wav")]

    file_count = len(wav_files)

    if file_count <= max_files:
        return 0  # nothing deleted

    # Sort by modification time (oldest first)
    wav_files.sort(key=os.path.getmtime)

    # Determine how many to delete
    to_delete = file_count - max_files

    deleted = 0
    for path in wav_files[:to_delete]:
        try:
            os.remove(path)
            deleted += 1
        except Exception as e:
            logger.debug(f"Failed to delete {path}: {e}")

    return deleted


#################### Setup ####################
# Display
lcd = lcddriver.LCD()
logger.debug(lcd.status_message)
lcd.lcd_clear()

# Display Startup ASCII-Art
lcd.lcd_display_string(r" - Bird Monitor 2 - ",2)
time.sleep(3)
lcd.lcd_display_string(r"    __      ___     ",1)
lcd.lcd_display_string(r"   / ;> \__/owo\    ",2)
lcd.lcd_display_string(r" -/_)')  \__)_/     ",3)
lcd.lcd_display_string(r"___/_/_____//_______",4)
time.sleep(4)
lcd.lcd_clear()
lcd.lcd_display_string(r" - Bird Monitor 2 - ",2)
lcd.lcd_display_string(r"Setup...",3)


#Weather Sensor
weather_sensor = WeatherSensor()



# Startup bird detection model
logger.debug('Loading labels...')
# Load the labels
try:
    with open(label_file, "r") as f:
        labels = f.read().splitlines()
except FileNotFoundError:
    logger.debug("Label file not found!")
    logger.debug("Terminating...")
    SystemExit(1)
# Get the model instance
logger.debug('Loading model...')
model_instance = model.Model(model_path=str(model_file), labels=labels)

# Start the LCDs display loop parallel to the mainloop
lcd_loop_thread = threading.Thread(target=lcd.mainloop, daemon=True)
lcd_loop_thread.start()

# Start reading from the microphone
microphone = microphone_server.Microphone_Server(audio_file_dir=audio_dir, device_id=mic_device_id,sample_rate_manual=sample_rate)
microphone_thread = threading.Thread(target=microphone.mainloop, daemon=True)
microphone_thread.start()

# Init Database
init_db()
###################################################
#################### MAIN LOOP ####################
###################################################
logger.debug("Entering main loop...")
try:
    while True:
        # Get audiofiles
        audiofiles = os.listdir(audio_dir)
        # Wait for new audiofiles if there are None
        if len(audiofiles) == 0:
            time.sleep(3)
            logger.debug("No files to process. Waiting...")
            continue

        # Process each file in the directory
        last_bird = "Empty"
        for filename in audiofiles:
            if filename.startswith("recording_") and filename.endswith(".wav"):
                # Get full filepath and open file
                filepath = os.path.join(audio_dir, filename)
                logger.debug(f"Opening file {filename}...")
                signal = audio.open_audio_file(filepath)
                signal = to_48k(signal)

                # Split the audiofile into the right sized chunks for the model
                logger.debug("Splitting signal...")
                chunks = audio.split_signal(signal, sample_rate=48000, seconds=3, overlap=0.0, min_len=2.0)

                # Run model for each chunk to get identification predictions
                logger.debug("Predicting...")
                for i in range(0, len(chunks)):
                    chunk = fix_length(chunks[i])
                    prediction = model_instance.predict(samples=chunks[i])
                    if prediction[0][2] > float(0.2):
                        last_bird = prediction[0][1]
                        last_bird = last_bird.split("_")[1]
                        # Get current date and time
                        current_date = dt.now().strftime('%Y-%m-%d')
                        current_time = dt.now().strftime('%H:%M:%S')
                        # Give the last detected bird over to the LCD
                        lcd.last_bird = last_bird
                        lcd.last_bird_timestamp = current_time
                        lcd.last_bird_updated = True
                        #TODO get weather info
                        weather_info = weather_sensor.read()
                        # Prepare data to write to CSV
                        ai_output = f"Chunk {i} from {filename}: {prediction}"
                        data_to_save = [current_date, current_time, ai_output, weather_info]
                        #Insert bird detection into db on website
                        insert_bird_detection(str(prediction[0][1]).split('_')[1])
                        logger.debug(f"Saved AI output to website db for chunk {i}.")
                        #Insert temperature into db on website
                        insert_temperature(weather_info["temperature"])
                        logger.debug(f"Saved last temperature to website db.")
                        # Write the data to CSV
                        #write_to_csv(data_to_save)
                        #logger.debug(f"Saved AI output and weather for chunk {i} to CSV.")
                # After processing, delete the file from the folder
                try:
                    filepath=Path(filepath)
                    filepath.unlink()
                    logger.debug("Deleted %s", filepath)
                    #safety check, deletes oldest files if there are too many
                    prune_wav_files()
                except FileNotFoundError:
                    logger.debug("File not found: %s", filepath)
                except PermissionError:
                    logger.debug("No permission to delete %s", filepath)
                # TODO SEND DATA TO WEBSITE PERIODICALLY
except Exception as e:
    logger.debug("Exception in main.py mainloop:")
    logger.debug(e)
    logger.debug("Shutting Down")
            
