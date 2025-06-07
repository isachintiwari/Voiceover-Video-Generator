# 🎙️ Voiceover Video Tool

Generate engaging videos with natural voiceovers from subtitle (`.srt`) files and optional background music — all through an easy-to-use Streamlit interface.

---

## 🚀 Features

- ✅ Upload an MP4 video and `.srt` subtitle file
- 🎤 Auto-generate voiceovers using Google Text-to-Speech (gTTS)
- 🎵 Add your own or select default background music
- 🎧 Preview the audio before download
- 📥 Download the final MP4 with merged voice and background music

---

## 🖥️ Live Demo

> [Streamlit Cloud](https://voiceover-video-generator-from-srt.streamlit.app/)

---

## 🛠️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/voiceover-video-tool.git
cd voiceover-video-tool
```

### 2. Create virtual environment (optional)
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install FFmpeg

- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: [Download from ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

---

## ▶️ Usage

```bash
streamlit run app.py
```

Upload your files in the sidebar, click **"Generate Voiceover"**, preview the audio, and download your final video.

---

## 📄 SRT Format Example

```srt
1
00:00:00,000 --> 00:00:05,000
Welcome! In this guide, you'll learn how to use this tool.

2
00:00:06,000 --> 00:00:10,000
Upload your video and subtitle file using the options on the left.
```

---

## 🙌 Credits

Made with ❤️ by [@isachintiwari](https://coff.ee/isachintiwari)

---

## 📄 License

MIT License
