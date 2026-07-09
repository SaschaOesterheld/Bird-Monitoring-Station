import socket
import wave
import time
import os
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOGGING_DIR_NAME = "logs"


class microphone_server:
    def __init__(self, audio_file_dir, logging_enabled=True, logger=None, udp_port=20208):
        # UDP port to listen on (where the microphone is on)
        self.UDP_PORT = udp_port
        # Create a UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind to all network interfaces on the given port
        self.sock.bind(('0.0.0.0', self.UDP_PORT))
        # Buffer to temporarily store incoming audio bytes
        self.buffer = []
        # Directory where WAV files will be saved
        self.save_dir = audio_file_dir
        os.makedirs(self.save_dir, exist_ok=True)  # Create directory if it doesn't exist
        # Setup logger
        self.logger_ = logger
        if not logger:
            # If no logger provided, create one
            self.logger_ = logging.getLogger(__name__)
            self.logger_.setLevel(logging.DEBUG)
            # Build log file path: BASE_DIR/logs/current_script_name.log
            log_file = BASE_DIR / LOGGING_DIR_NAME / Path(__file__).stem + ".log"
            self.logger_.addHandler(logging.FileHandler(log_file))
        # Enable or disable logging based on argument
        self.logger_.disabled = not logging_enabled

    def main_loop(self):
        """
        Main loop that continuously receives UDP audio data,
        save it to a buffer, and writes it to a WAV file when enough data is collected.
        """
        while True:
            # Receive data from any client; buffer size is 48000 bytes
            try:
                data, addr = self.sock.recvfrom(48000)  # receive UDP packet
            except socket.timeout:
                self.logger_.warning("Socket timeout")
                time.sleep(1)
                continue
            # Append each byte in received data to buffer
            self.buffer.extend(data)
            # Once buffer reaches the size of 18 seconds of audio at 48kHz, 16-bit mono
            # Calculation: 18 seconds * 2 bytes/sample * 48000 samples/sec
            if len(self.buffer) >= 18 * 2 * 48000:
                self.logger_.debug("Write to file...")
                # Generate a timestamped filename
                timestamp = int(time.time())
                filename = f"sound_{timestamp}.wav"
                # Combine directory and filename
                filepath = os.path.join(self.save_dir, filename)
                # Open a WAV file for writing
                with wave.open(filepath, "wb") as out_f:
                    out_f.setnchannels(1)  # Mono
                    out_f.setsampwidth(2)  # 2 bytes per sample (16-bit)
                    out_f.setframerate(48000)  # 48 kHz sample rate
                    out_f.writeframesraw(bytes(self.buffer))  # Write buffered audio
                # Clear buffer after writing
                self.buffer.clear()
                # Log file save
                self.logger_.debug(f"File saved at {filepath}")
