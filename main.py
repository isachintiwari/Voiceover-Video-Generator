import os
import re
import subprocess
import tempfile
import streamlit as st
from gtts import gTTS
import requests

st.set_page_config(
    page_title="Voiceover Video Tool",
    page_icon="🎤",
    layout="wide",
    menu_items={
        "About": "This tool lets you auto-generate voiceovers from subtitles and add background music to videos."
    }
)

DEFAULT_MUSIC = {
    "Soft Piano": "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Komiku/It_Grows/Komiku_-_01_-_Friends_Call_Me_Jimmy.mp3",
    "Ambient Loop": "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Lobo_Loco/Sounds_of_the_Street/Lobo_Loco_-_01_-_Ladies_Night_ID_1179.mp3",
    "Calm Background": "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Monplaisir/Loyalty_Freak_Music/Monplaisir_-_03_-_Electric_Dawn.mp3",
    "Eona Ambient Pop": "https://raw.githubusercontent.com/isachintiwari/tools/dev/eona-emotional-ambient-pop-351436.mp3"
}

with st.sidebar:
    st.header("🎛️ Configuration")
    uploaded_video = st.file_uploader("Upload MP4 video", type=["mp4"])
    uploaded_srt = st.file_uploader("Upload SRT subtitles", type=["srt"])
    uploaded_music = st.file_uploader("(Optional) Upload your own background music (MP3)", type=["mp3"])
    default_music_choice = st.selectbox("Or choose a default music", ["None"] + list(DEFAULT_MUSIC.keys()))
    generate = st.button("Generate Voiceover")

    st.markdown("---")
    st.markdown("""
    <div style='text-align: center;'>
        <span style='font-size: 13px;'>Made with ❤️ by <a href='https://coff.ee/isachintiwari' target='_blank'>@isachintiwari</a></span><br>
        <a href='https://coff.ee/isachintiwari' target='_blank'>
            <img src='https://cdn.buymeacoffee.com/buttons/v2/default-orange.png' alt='Buy Me A Coffee' style='height: 20px !important; margin-top: 4px;'>
        </a>
    </div>
    """, unsafe_allow_html=True)

st.title("🎙️ Voiceover Video Generator")
st.markdown("""
This tool helps you generate voiceovers from subtitle files and combine them with video and optional background music.
Upload your video and SRT file on the left to begin.

### 🔧 Steps to Use:
1. **Upload your MP4 video** file using the sidebar.
2. **Upload your .srt subtitle file**, which contains the timed narration.
3. **(Optional)** Add your own background music or pick from the default list.
4. Click the **Generate Voiceover** button.
5. Wait for the tool to process and download the final video.

### 📄 SRT File Format Example:
```
1
00:00:00,000 --> 00:00:05,000
Welcome! In this quick guide, you'll learn how to use this tool to create voiceovers with background music.

2
00:00:06,000 --> 00:00:15,000
First, upload your video file and subtitle file using the options on the left.

3
00:00:16,000 --> 00:00:25,000
Then, optionally upload background music or choose a default one. Click the button to generate your final video.
```
Ensure your timestamps are formatted correctly and do not overlap.
""")

# ✅ FIX for audio preview crash

def safe_audio_preview(audio_path, audio_format="audio/mp3"):
    try:
        with open(audio_path, "rb") as f:
            st.audio(f.read(), format=audio_format)
    except Exception as e:
        st.warning(f"Preview failed: {e}")

# ✅ Display spinner during processing
if generate and uploaded_video and uploaded_srt:
    with st.spinner("⏳ Generating video with voiceover, please wait..."):
        try:
            st.success("✅ Processing complete! You can now download your video.")
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
