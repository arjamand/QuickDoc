import whisper
import sounddevice as sd
import numpy as np
import warnings
import scipy.io.wavfile as wav
import os

# Suppress specific warnings
warnings.filterwarnings("ignore", message="You are using `torch.load` with `weights_only=False`")
warnings.filterwarnings("ignore", category=UserWarning)

# Load the Whisper model
model = whisper.load_model("base")

def list_mics():
    """
    List all available audio input devices (microphones).
    """
    print("Available Microphones:")
    devices = sd.query_devices()
    input_devices = [device for device in devices if device['max_input_channels'] > 0]
    
    for idx, device in enumerate(input_devices):
        print(f"{idx}: {device['name']} (Channels: {device['max_input_channels']})")
    
    return input_devices

def select_microphone():
    """
    Prompt user to select a microphone from the list of available microphones.
    """
    input_devices = list_mics()
    while True:
        try:
            device_index = int(input("Select the microphone (enter the index number): "))
            if 0 <= device_index < len(input_devices):
                return input_devices[device_index], device_index
            else:
                print("Invalid index, please try again.")
        except ValueError:
            print("Invalid input, please enter a number.")

def transcribe_continuous_with_filter(sample_rate=16000, duration=5):
    """
    Continuously records and transcribes audio with noise filtering until the user types 'exit'.
    :param sample_rate: Audio sample rate (default is 16kHz for Whisper)
    :param duration: Maximum recording duration in seconds
    """
    print("Type 'exit' to end the session. Press Enter to start recording.")

    # Select microphone
    selected_device, device_index = select_microphone()
    print(f"Using microphone: {selected_device['name']}")

    while True:
        command = input("\nReady to record? (Press Enter to start or type 'exit' to quit): ")
        if command.lower() == "exit":
            print("Exiting transcription session. Goodbye!")
            break

        print(f"Recording for up to {duration} seconds... Press Enter to stop early.")

        # Start recording
        recording = []
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            recording.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=sample_rate, 
                channels=1, 
                device=device_index, 
                callback=audio_callback
            ):
                # Wait for user input or timeout
                sd.sleep(duration * 1000)  # Convert seconds to milliseconds
        except sd.PortAudioError as e:
            print(f"Audio input error: {e}")
            continue

        # Combine recorded chunks into a single audio array
        if not recording:
            print("No audio recorded. Please try again.")
            continue

        audio_data = np.concatenate(recording, axis=0)
        audio_data = np.squeeze(audio_data)  # Remove extra dimensions

        # Normalize audio
        audio_data = audio_data.astype(np.float32)
        audio_data = audio_data / np.max(np.abs(audio_data))

        # Save audio for debugging
        wav.write('recorded_audio.wav', sample_rate, (audio_data * 32767).astype(np.int16))

        print(f"Audio data captured, length: {len(audio_data)} samples")

        # Transcribe the audio
        try:
            print("Transcribing...")
            result = model.transcribe(audio_data, language="en", fp16=False)
            transcription = result.get("text", "").strip()

            if transcription:
                print("Transcription:", transcription)
            else:
                print("No speech detected or transcription is empty.")
        except Exception as e:
            print(f"Transcription error: {e}")

if __name__ == "__main__":
    transcribe_continuous_with_filter()
