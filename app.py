import tkinter
import customtkinter
import sounddevice as sd
import numpy as np
import whisper
import os
import time
from datetime import datetime
import win32com.client  # For MS Word integration

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class WhisperASRApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Whisper ASR Transcription")
        self.geometry("1300x800")

        # Load Whisper model
        self.model = whisper.load_model("base")  # Choose model size: tiny, base, small, medium, large

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

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
        self.microphones = sd.query_devices()
        mic_names = [device['name'] for device in self.microphones if device['max_input_channels'] > 0]
        
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
            width=BUTTON_WIDTH-100
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

        # Save Document Button
        self.save_button = customtkinter.CTkButton(
            self.sidebar_frame, 
            text="Save Document", 
            command=self.save_document,
            width=BUTTON_WIDTH
        )
        self.save_button.grid(row=5, column=0, padx=15, pady=10)

        # Appearance Mode
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=15, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame, 
            values=["Light", "Dark", "System"],
            width=BUTTON_WIDTH,
            command=self.change_appearance_mode_event
        )
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=15, pady=(10, 10))

        # UI Scaling
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=8, column=0, padx=15, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame, 
            values=["80%", "90%", "100%", "110%", "120%"],
            width=BUTTON_WIDTH,
            command=self.change_scaling_event
        )
        self.scaling_optionemenu.grid(row=9, column=0, padx=15, pady=(10, 20))

        # Main area for transcription and document
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Transcription area
        self.transcription_label = customtkinter.CTkLabel(self.main_frame, text="Transcription")
        self.transcription_label.grid(row=0, column=0, padx=10, pady=(0, 5), sticky="w")
        
        self.transcription_textbox = customtkinter.CTkTextbox(self.main_frame, width=800, height=300)
        self.transcription_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.transcription_textbox.insert("0.0", "Transcription will appear here...")

        # Word Document Viewer (if possible with tkinter)
        self.doc_label = customtkinter.CTkLabel(self.main_frame, text="Document Template")
        self.doc_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.doc_textbox = customtkinter.CTkTextbox(self.main_frame, width=800, height=300)
        self.doc_textbox.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.doc_textbox.insert("0.0", "MS Word Document will be displayed here...")

        # Set default values
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")

        # Recording state variables
        self.is_recording = False
        self.selected_mic_index = 0
        self.recording_start_time = None
        self.audio_data = []

    def select_microphone(self, selected_mic):
        self.selected_mic_index = mic_names.index(selected_mic)

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
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(status)
            self.audio_data.append(indata.copy())
            elapsed_time = time.time() - self.recording_start_time
            minutes, seconds = divmod(int(elapsed_time), 60)
            self.record_time_label.configure(text=f"{minutes:02d}:{seconds:02d}")

        self.stream = sd.InputStream(
            device=self.selected_mic_index, 
            channels=1, 
            callback=audio_callback
        )
        self.stream.start()

    def stop_recording(self):
        self.is_recording = False
        self.record_button.configure(text="Start Recording")
        self.stream.stop()
        self.stream.close()
        
        # Convert recorded audio
        audio_array = np.concatenate(self.audio_data, axis=0)
        audio_array = audio_array.flatten()
        
        # Transcribe with Whisper
        try:
            result = self.model.transcribe(audio_array)
            self.transcription_textbox.delete("0.0", "end")
            self.transcription_textbox.insert("0.0", result['text'])
        except Exception as e:
            self.transcription_textbox.delete("0.0", "end")
            self.transcription_textbox.insert("0.0", f"Transcription Error: {str(e)}")

    def embed_transcription(self):
        current_doc = self.doc_textbox.get("0.0", "end")
        transcription = self.transcription_textbox.get("0.0", "end")
        
        updated_doc = current_doc + "\n\n" + transcription
        self.doc_textbox.delete("0.0", "end")
        self.doc_textbox.insert("0.0", updated_doc)

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