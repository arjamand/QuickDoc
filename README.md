# QuickDoc

This project provides a set of tools for audio transcription using Whisper ASR, with a focus on integration with document editing workflows. It features a user-friendly interface built with `customtkinter` and includes functionality for recording audio, transcribing it, and embedding the transcriptions into a document template.

## Project Structure
```
├── .gitattributes
├── README.md
├── app-v2.py
├── app-v3.py
├── app-v4.py
├── app.py
├── main.cpp
├── requirements.txt
├── template.png
├── template_doc.docx
├── transcription_20241213_174322.txt
├── v2.py
├── v3.py
├── v4.py
├── v6-german.py
├── whisper-asr-v5.py
├── whisper_asr.ipynb
├── whisper_asr.py
└── whisper_continuous_with_filter.py
```

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/arjamand/QuickDoc.git
    cd QuickDoc
    ```
2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

To run the application, execute the following command in the project root folder:

```bash
python app-v4.py
```
or
```bash
python app-v2.py
```

## Usage
1. **Select Microphone**: Choose your desired microphone from the dropdown.
2. **Start/Stop Recording**: Click the "Start Recording" button to begin audio capture, and click "Stop Recording" to end it.
3. **View Transcription**: The transcribed text will appear in the "Transcription" text box.
4. **Embed Transcription**: Click "Embed Transcription" to add the transcribed text to the document.
5. **Print/Save Document**: Use the "Print Document" or "Save Document" buttons to manage the final document.
6. **Adjust UI**: Use the "Appearance Mode" and "UI Scaling" dropdowns to customize the user interface.

## Notes

- Make sure to select a valid microphone in the dropdown before starting to record.
- The application utilizes a base Whisper model. Other model sizes can be loaded by modifying the `whisper.load_model()` argument.
-  `app-v4.py` loads an image for better UI experience. The default `template.png` file or an updated image can be provided to the application.
- The `main.cpp` provides a way to test pybind11 with whisper module.

## Contributing

Feel free to contribute to the project by submitting issues, or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
