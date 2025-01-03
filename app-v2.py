import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter
import sounddevice as sd
import numpy as np
import whisper
import os
import time
from datetime import datetime
import win32com.client  # For MS Word integration
import threading
import queue
import warnings
from docx import Document

warnings.filterwarnings("ignore", category=UserWarning)

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

# Load Whisper model (outside class for performance)
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
        return input_devices

    def select_microphone(self, input_devices, selected_mic_index):
        """Select a microphone."""
        return input_devices[selected_mic_index], selected_mic_index

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


class WhisperASRApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Whisper ASR Transcription")
        self.geometry("1150x650")
        self.audio_recorder = AudioRecorder()
        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        # Loading widgets
        self.loading_window = None
        # Create sidebar frame
        self.sidebar_frame = customtkinter.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        # Consistent button width
        BUTTON_WIDTH = 220
        BUTTON_HEIGHT = 40

        # App title
        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Whisper ASR",
            font=customtkinter.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=15, pady=(20, 10))

        # Microphone selection dropdown
        self.mic_label = customtkinter.CTkLabel(self.sidebar_frame, text="Select Microphone:")
        self.mic_label.grid(row=1, column=0, padx=15, pady=(10, 5))

        # Get available microphones
        self.microphones = self.audio_recorder.list_microphones()
        mic_names = [device['name'] for device in self.microphones]

        self.mic_dropdown = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=mic_names,
            width=BUTTON_WIDTH,
            command=self.select_microphone
        )
        self.mic_dropdown.grid(row=2, column=0, padx=15, pady=(0, 10))

        # Recording controls frame
        self.recording_frame = customtkinter.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.recording_frame.grid(row=3, column=0, padx=15, pady=10, sticky="ew")
        self.recording_frame.grid_columnconfigure(1, weight=1)

        # Recording button
        self.record_button = customtkinter.CTkButton(
            self.recording_frame,
            text="Start Recording",
            command=self.toggle_recording,
            width=BUTTON_WIDTH - 100
        )
        self.record_button.grid(row=0, column=0, padx=(0, 5))

        # Recording time display
        self.record_time_label = customtkinter.CTkLabel(
            self.recording_frame,
            text="00:00",
            font=customtkinter.CTkFont(size=14),
            fg_color=self.record_button.cget("fg_color"),
            corner_radius=self.record_button.cget("corner_radius")
        )
        self.record_time_label.grid(row=0, column=1, sticky="ew")

        # Embed Transcription Button
        self.embed_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Embed Transcription",
            command=self.embed_transcription,
            width=BUTTON_WIDTH
        )
        self.embed_button.grid(row=4, column=0, padx=15, pady=10)
        # Print Document Button
        self.print_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Print Document",
            command=self.print_document,
            width=BUTTON_WIDTH
        )
        self.print_button.grid(row=5, column=0, padx=15, pady=10)

        # Save Document Button
        self.save_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Save Document",
            command=self.save_document,
            width=BUTTON_WIDTH
        )
        self.save_button.grid(row=6, column=0, padx=15, pady=10)
         # Create a frame to hold scaling and appearance options
        self.settings_frame = customtkinter.CTkFrame(self.sidebar_frame)
        self.settings_frame.grid(row=11, column=0, padx=15, pady=10, sticky="ew")
        self.settings_frame.grid_columnconfigure(0, weight=1)

        # Appearance Mode
        self.appearance_mode_label = customtkinter.CTkLabel(self.settings_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=0, column=0, padx=0, pady=(0, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            self.settings_frame,
            values=["Light", "Dark", "System"],
            width=BUTTON_WIDTH,
            command=self.change_appearance_mode_event
        )
        self.appearance_mode_optionemenu.grid(row=1, column=0, padx=0, pady=(0, 10))
        # UI Scaling
        self.scaling_label = customtkinter.CTkLabel(self.settings_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=2, column=0, padx=0, pady=(0, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(
            self.settings_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            width=BUTTON_WIDTH,
            command=self.change_scaling_event
        )
        self.scaling_optionemenu.grid(row=3, column=0, padx=0, pady=(0, 0))
        # Main area for transcription and document
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Transcription area
        self.transcription_label = customtkinter.CTkLabel(self.main_frame, text="Transcription")
        self.transcription_label.grid(row=0, column=0, padx=10, pady=(0, 5), sticky="w")

        self.transcription_textbox = customtkinter.CTkTextbox(self.main_frame, width=800, height=180)
        self.transcription_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.transcription_textbox.insert("0.0", "Transcription will appear here...")

        # Word Document Viewer (if possible with tkinter)
        self.doc_label = customtkinter.CTkLabel(self.main_frame, text="Document Template")
        self.doc_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")

        self.doc_textbox = customtkinter.CTkTextbox(self.main_frame, width=800, height=420)
        self.doc_textbox.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.load_document_template("template_doc.docx")

        # Set default values
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")

        # Recording state variables
        self.is_recording = False
        self.selected_mic_index = 0
        self.recording_start_time = None
        self.audio_data = []

    def show_loading(self, message="Loading..."):
        if self.loading_window is not None:  # If there's already a loading window, close it before opening a new one
           self.loading_window.destroy()
        self.loading_window = tk.Toplevel(self)
        self.loading_window.title("Please Wait")
        self.loading_window.geometry("300x100")
        self.loading_window.resizable(False, False)
        
        loading_label = tk.Label(self.loading_window, text=message, font=("Arial", 12))
        loading_label.pack(pady=30)
        self.loading_window.transient(self)  # Set the loading window as a transient of the main window
        self.loading_window.grab_set()  # Grab focus to prevent interaction with the main window

        # Make sure the loading window is always on top of the main window
        self.loading_window.attributes("-topmost", True)
    def hide_loading(self):
      if self.loading_window:
          self.loading_window.destroy()
          self.loading_window = None
    def select_microphone(self, selected_mic):
      try:
        self.selected_mic_index = [device['name'] for device in self.microphones].index(selected_mic)
      except ValueError:
        messagebox.showerror("Microphone Error", "Selected microphone is no longer available. Please select a different one.")
        return
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.record_button.configure(text="Stop Recording")
        self.audio_data = []
        self.recording_start_time = time.time()

        self.audio_recorder.start_recording(self.selected_mic_index)
        self.update_record_time()

    def update_record_time(self):
      if self.is_recording:
          elapsed_time = time.time() - self.recording_start_time
          minutes, seconds = divmod(int(elapsed_time), 60)
          self.record_time_label.configure(text=f"{minutes:02d}:{seconds:02d}")
          self.after(100, self.update_record_time)

    def stop_recording(self):
      self.is_recording = False
      self.record_button.configure(text="Start Recording")
      self.record_time_label.configure(text="00:00")  # Reset time display
      audio_data = self.audio_recorder.stop_recording()
      if audio_data is not None:
        self.transcribe_audio(audio_data)

    def transcribe_audio(self, audio_data):
       self.show_loading(message="Transcribing...")
       threading.Thread(target=self._transcribe_audio_thread, args=(audio_data,), daemon=True).start()
    def _transcribe_audio_thread(self, audio_data):
       transcription = self.audio_recorder.transcribe_audio(audio_data)
       self.after(0, self._update_transcription_ui, transcription)  # Use after to update the UI
    def _update_transcription_ui(self, transcription):
       self.transcription_textbox.delete("0.0", "end")
       self.transcription_textbox.insert("0.0", transcription)
       self.hide_loading()


    def embed_transcription(self):
        transcription = self.transcription_textbox.get("0.0", "end")
        current_doc = self.doc_textbox.get("0.0", "end")
        updated_doc = current_doc + "\n\n" + transcription
        self.doc_textbox.delete("0.0", "end")
        self.doc_textbox.insert("0.0", updated_doc)

    def load_document_template(self, doc_path):
          try:
            doc = Document(doc_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            self.doc_textbox.delete("0.0", "end")
            self.doc_textbox.insert("0.0", text)
          except Exception as e:
             self.doc_textbox.delete("0.0", "end")
             self.doc_textbox.insert("0.0", f"Error loading document: {e}")
    def print_document(self):
          try:
             # Open MS Word
             word = win32com.client.Dispatch("Word.Application")
             word.Visible = False
             doc = word.Documents.Add()

             # Get document content
             content = self.doc_textbox.get("0.0", "end")
             doc.Content.Text = content
             doc.PrintOut()
             # Close document and word application
             doc.Close(False)
             word.Quit()

          except Exception as e:
            tkinter.messagebox.showerror("Printing Error", str(e))
    def save_document(self):
        try:
            # Open MS Word
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Add()

            # Get document content
            content = self.doc_textbox.get("0.0", "end")
            doc.Content.Text = content

            # Save document
            filename = f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            doc.SaveAs(filename)

            # Close document and word application
            doc.Close()
            word.Quit()

            tkinter.messagebox.showinfo("Save Successful", f"Document saved as {filename}")
        except Exception as e:
            tkinter.messagebox.showerror("Save Error", str(e))

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)


def main():
    app = WhisperASRApp()
    app.mainloop()


if __name__ == "__main__":
    main()