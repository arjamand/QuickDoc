import whisper
import sounddevice as sd
import numpy as np
import warnings
import os

# Suppress the specific PyTorch warning about pickle loading
warnings.filterwarnings("ignore", message="You are using `torch.load` with `weights_only=False`")

# Load the Whisper model
model = whisper.load_model("base")  # Removed the weights_only argument

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
                return input_devices[device_index]['name']
            else:
                print("Invalid index, please try again.")
        except ValueError:
            print("Invalid input, please enter a number.")

def transcribe_continuous_with_filter(sample_rate=16000):
    """
    Continuously records and transcribes audio with noise filtering until the user types 'exit'.
    :param sample_rate: Audio sample rate (default is 16kHz for Whisper).
    :return: None (prints transcriptions).
    """
    print("Type 'exit' to end the session. Press Enter to start recording.")

    # Select microphone
    selected_microphone = select_microphone()
    print(f"Using microphone: {selected_microphone}")

    while True:
        command = input("\nReady to record? (Press Enter to start or type 'exit' to quit): ")
        if command.lower() == "exit":
            print("Exiting transcription session. Goodbye!")
            break

        print("Recording... Press Enter to stop.")

        # Start recording
        recording = []
        device_index = next(idx for idx, device in enumerate(sd.query_devices()) if device['name'] == selected_microphone)
        stream = sd.InputStream(samplerate=sample_rate, channels=1, device=device_index, callback=lambda indata, frames, time, status: recording.append(indata.copy()))
        
        with stream:
            input()  # Wait for the user to press Enter to stop recording
            print("Recording stopped.")

        # Combine recorded chunks into a single audio array
        audio_data = np.concatenate(recording, axis=0)
        audio_data = np.squeeze(audio_data)  # Remove extra dimensions

        import scipy.io.wavfile as wav
        # Save audio to a file for debugging
        wav.write('recorded_audio.wav', sample_rate, audio_data)

        # Check if audio is being recorded correctly (debugging)
        print(f"Audio data captured, length: {len(audio_data)} samples")

        # Convert to float32 in the range [-1, 1]
        audio_data = audio_data.astype(np.float32) / 32768.0

        # Ensure audio is non-empty before passing to the model
        if audio_data.size == 0:
            print("No audio captured. Please try again.")
            continue

        # Transcribe the audio
        print("Transcribing...")
        result = model.transcribe(audio_data, language="en")
        transcription = result.get("text", "")

        # os.system("whisper 'recorded_audio.wav' --model base")
        
        if transcription.strip():
            print("Transcription:", transcription)
        else:
            print("No speech detected. Please try again.")

transcribe_continuous_with_filter()
