"""
Audio processing utilities for the Bird Monitor system.

This module provides helper functions for loading, saving, splitting,
and visualizing audio recordings. The utilities are primarily used to
prepare microphone recordings for BirdNET inference and to assist with
debugging by plotting waveforms and spectrograms.
"""

import librosa
import soundfile
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal


def open_audio_file(path: str, sample_rate=48000, offset=0.0, duration=None):
    """
    Load an audio file.

    The audio is converted to mono and resampled to the requested sample
    rate.

    Args:
        path: Path to the audio file.
        sample_rate: Desired output sample rate.
        offset: Start time in seconds.
        duration: Maximum duration to load in seconds.

    Returns:
        Audio samples as a NumPy array.
    """
    samples, sr = librosa.load(path, sr=sample_rate, mono=True, offset=offset, duration=duration)
    return samples


def save_signal(filename: str, sig):
    """
    Save an audio signal as a WAV file.

    Args:
        filename: Output file path.
        sig: Audio samples to save.
    """
    soundfile.write(filename, sig, 48000)
    return


def split_signal(sig: np.ndarray, sample_rate: int, seconds: float, overlap: float, min_len: float):
    """
    Split an audio signal into overlapping chunks.

    If the final chunk is shorter than the specified minimum length,
    Gaussian noise is appended so that the chunk reaches the desired size.

    Args:
        sig: Audio signal.
        sample_rate: Sampling rate in Hz.
        seconds: Length of each chunk in seconds.
        overlap: Fractional overlap between consecutive chunks in the
            range [0, 1).
        min_len: Minimum chunk length in seconds before padding.

    Returns:
        A list of audio chunks.
    """
    chunk_size = int(sample_rate * seconds)
    step_size = int(chunk_size * (1 - overlap))
    chunks = [sig[i:i + chunk_size] for i in range(0, len(sig), step_size)]
    if len(chunks[-1]) < min_len * sample_rate:
        noise = np.random.normal(0, 0.1, chunk_size - len(chunks[-1]))
        chunks[-1] = np.concatenate([chunks[-1], noise])
    return chunks


def plot_chunk(chunk, sr, chunk_num):
    """
    Plot the waveform of an audio chunk.

    Args:
        chunk: Audio samples.
        sr: Sampling rate in Hz.
        chunk_num: Chunk identifier used in the plot title.
    """
    time = np.linspace(0, len(chunk) / sr, num=len(chunk))  # time axis
    plt.figure(figsize=(10, 4))
    plt.plot(time, chunk)
    plt.title(f"Audio Chunk {chunk_num}")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")
    plt.show()


def plot_chunk_spectrum(chunk, sr):
    """
    Display the spectrogram of an audio chunk.

    Args:
        chunk: Audio samples.
        sr: Sampling rate in Hz.
    """
    f, t, sxx = signal.spectrogram(chunk, sr)
    plt.figure(figsize=(10, 6))
    plt.pcolormesh(t, f, 10 * np.log10(sxx), shading='gouraud')
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    plt.title('Spectrogram of Test Signal')
    plt.colorbar(label='Intensity [dB]')
    plt.show()
