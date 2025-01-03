import wave
import pyaudio
import os

# Configuration for audio recording
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
AUDIO_FILE = "recorded_audio.wav"  # File to save the recording
CONVERTED_FILE = "recorded_audio.mp3"  # File to save the converted audio (for Whisper)

def record_audio():
    """Record audio until the user stops."""
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("Recording... Press Enter to stop.")
    frames = []

    try:
        while True:
            data = stream.read(CHUNK)
            frames.append(data)
    except KeyboardInterrupt:
        print("\nRecording stopped.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    # Save the recorded audio
    with wave.open(AUDIO_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    
    print(f"Audio saved to {AUDIO_FILE}")

def convert_to_mp3():
    """Convert WAV file to MP3 using FFmpeg."""
    print("Converting to MP3...")
    os.system(f"ffmpeg -i {AUDIO_FILE} {CONVERTED_FILE} -y")
    print(f"Converted to {CONVERTED_FILE}")

def run_whisper():
    """Run the Whisper model on the recorded MP3 file."""
    print("Running Whisper...")
    os.system(f"whisper {CONVERTED_FILE} --model base")

if __name__ == "__main__":
    print("Press Enter to start recording...")
    input()
    try:
        record_audio()
        convert_to_mp3()
        run_whisper()
    except Exception as e:
        print(f"An error occurred: {e}")
