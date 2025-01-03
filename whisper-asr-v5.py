import whisper
import sounddevice as sd
import numpy as np
import warnings
import queue
import threading
import time

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Load the Whisper model
model = whisper.load_model("base")

class AudioRecorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_queue = queue.Queue()
        self.thread = None

    def list_microphones(self):
        """List all available audio input devices."""
        devices = sd.query_devices()
        input_devices = [dev for dev in devices if dev['max_input_channels'] > 0]
        
        print("Available Microphones:")
        for idx, device in enumerate(input_devices):
            print(f"{idx}: {device['name']} (Channels: {device['max_input_channels']})")
        
        return input_devices

    def select_microphone(self, input_devices):
        """Prompt user to select a microphone."""
        while True:
            try:
                device_index = int(input("Select microphone (index): "))
                if 0 <= device_index < len(input_devices):
                    return input_devices[device_index], device_index
                print("Invalid index, please try again.")
            except ValueError:
                print("Invalid input, please enter a number.")

    def audio_callback(self, indata, frames, time, status):
        """Callback to store audio data."""
        if status:
            print(f"Status: {status}")
        if self.recording:
            self.audio_queue.put(indata.copy())

    def start_recording(self, device_index):
        """Start audio recording."""
        self.recording = True
        self.audio_queue = queue.Queue()
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate, 
                channels=1, 
                device=device_index, 
                callback=self.audio_callback
            )
            self.stream.start()
            print("\nRecording... (Press Enter to stop)")
        except sd.PortAudioError as e:
            print(f"Audio input error: {e}")
            self.recording = False

    def stop_recording(self):
        """Stop audio recording and collect audio data."""
        if not self.recording:
            return None

        self.recording = False
        self.stream.stop()
        
        # Collect audio data from queue
        audio_chunks = []
        while not self.audio_queue.empty():
            audio_chunks.append(self.audio_queue.get())
        
        if not audio_chunks:
            print("No audio recorded.")
            return None

        # Combine and normalize audio
        audio_data = np.concatenate(audio_chunks, axis=0)
        audio_data = np.squeeze(audio_data).astype(np.float32)
        audio_data = audio_data / np.max(np.abs(audio_data))
        
        return audio_data

    def transcribe_audio(self, audio_data):
        """Transcribe audio using Whisper."""
        if audio_data is None or len(audio_data) == 0:
            return ""

        try:
            result = model.transcribe(audio_data, language="de", fp16=False)
            return result.get("text", "").strip()
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

def main():
    recorder = AudioRecorder()
    
    print("Type 'exit' to end the session.")
    
    # Select microphone
    input_devices = recorder.list_microphones()
    selected_device, device_index = recorder.select_microphone(input_devices)
    print(f"Using microphone: {selected_device['name']}")

    while True:
        # Wait for user to start recording
        command = input("\nPress Enter to start recording or type 'exit': ")
        
        if command.lower() == 'exit':
            print("Exiting transcription session. Goodbye!")
            break

        # Start recording
        recorder.start_recording(device_index)
        
        # Wait for user to stop recording
        input()
        
        # Stop recording and get audio data
        audio_data = recorder.stop_recording()
        
        # Transcribe if audio was recorded
        if audio_data is not None:
            print("\nTranscribing...")
            transcription = recorder.transcribe_audio(audio_data)
            
            if transcription:
                print("Transcription:", transcription)
            else:
                print("No speech detected or transcription is empty.")

if __name__ == "__main__":
    main()