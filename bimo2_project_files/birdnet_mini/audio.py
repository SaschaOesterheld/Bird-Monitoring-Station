import librosa
import soundfile
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal


def open_audio_file(path: str, sample_rate=48000, offset=0.0, duration=None):
    samples, sr = librosa.load(path, sr=sample_rate, mono=True, offset=offset, duration=duration)
    return samples


def save_signal(filename: str, sig):
    soundfile.write(filename, sig, 48000)
    return


def split_signal(sig: np.ndarray, sample_rate: int, seconds: float, overlap: float, min_len: float):
    chunk_size = int(sample_rate * seconds)
    step_size = int(chunk_size * (1 - overlap))
    chunks = [sig[i:i + chunk_size] for i in range(0, len(sig), step_size)]
    if len(chunks[-1]) < min_len * sample_rate:
        noise = np.random.normal(0, 0.1, chunk_size - len(chunks[-1]))
        chunks[-1] = np.concatenate([chunks[-1], noise])
    return chunks


def plot_chunk(chunk, sr, chunk_num):
    time = np.linspace(0, len(chunk) / sr, num=len(chunk))  # time axis
    plt.figure(figsize=(10, 4))
    plt.plot(time, chunk)
    plt.title(f"Audio Chunk {chunk_num}")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")
    plt.show()


def plot_chunk_spectrum(chunk, sr):
    f, t, sxx = signal.spectrogram(chunk, sr)
    plt.figure(figsize=(10, 6))
    plt.pcolormesh(t, f, 10 * np.log10(sxx), shading='gouraud')
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    plt.title('Spectrogram of Test Signal')
    plt.colorbar(label='Intensity [dB]')
    plt.show()
