import os
import re
import subprocess
import tempfile
import streamlit as st
from gtts import gTTS
import requests
from pydub import AudioSegment

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

def parse_srt(file_content):
    entries = []
    blocks = re.split(r"\n\n", file_content.strip())
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            times = lines[1].split(" --> ")
            text = " ".join(lines[2:])
            entries.append((times[0], times[1], text))
    return entries

def time_to_seconds(t):
    h, m, s = t.replace(",", ".").split(":")
    return int(h)*3600 + int(m)*60 + float(s)

def generate_tts_clip(text, path):
    tts = gTTS(text)
    tts.save(path)

def combine_audio_clips(srt_entries, output_audio_path):
    combined = AudioSegment.silent(duration=0)
    for idx, (start, end, text) in enumerate(srt_entries):
        start_ms = int(time_to_seconds(start) * 1000)
        end_ms = int(time_to_seconds(end) * 1000)
        duration_ms = end_ms - start_ms

        tts_path = tempfile.mktemp(suffix=".mp3")
        generate_tts_clip(text, tts_path)
        clip = AudioSegment.from_file(tts_path)

        if len(clip) < duration_ms:
            clip += AudioSegment.silent(duration=(duration_ms - len(clip)))
        else:
            clip = clip[:duration_ms]

        silence_before = start_ms - len(combined)
        if silence_before > 0:
            combined += AudioSegment.silent(duration=silence_before)

        combined += clip

    combined.export(output_audio_path, format="mp3")
    return output_audio_path

def merge_audio_music(voice_path, music_path, output_path):
    subprocess.run([
        "ffmpeg", "-i", voice_path, "-i", music_path, "-filter_complex",
        "[0:a]volume=1.5[a0];[1:a]volume=0.3[a1];[a0][a1]amix=inputs=2:duration=longest",
        "-c:a", "aac", "-shortest", output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def merge_audio_video(video_path, audio_path, output_path):
    subprocess.run([
        "ffmpeg", "-i", video_path, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-shortest", output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
            <img src='https://cdn.buymeacoffee.com/buttons/v2/default-orange.png' alt='Buy Me A Coffee' style='height: 18px !important; margin-top: 4px;'>
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

if generate and uploaded_video and uploaded_srt:
    with st.spinner("⏳ Generating video with voiceover, please wait..."):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as v_tmp:
                v_tmp.write(uploaded_video.read())
                video_path = v_tmp.name

            srt_text = uploaded_srt.read().decode("utf-8")
            entries = parse_srt(srt_text)

            voice_path = tempfile.mktemp(suffix=".mp3")
            combine_audio_clips(entries, voice_path)

            if uploaded_music:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as m_tmp:
                    m_tmp.write(uploaded_music.read())
                    music_path = m_tmp.name
            elif default_music_choice != "None":
                music_url = DEFAULT_MUSIC[default_music_choice]
                music_path = tempfile.mktemp(suffix=".mp3")
                r = requests.get(music_url)
                with open(music_path, "wb") as f:
                    f.write(r.content)
            else:
                music_path = None

            final_audio = tempfile.mktemp(suffix=".aac")
            if music_path:
                merge_audio_music(voice_path, music_path, final_audio)
            else:
                final_audio = voice_path

            final_video = tempfile.mktemp(suffix=".mp4")
            merge_audio_video(video_path, final_audio, final_video)

            st.success("✅ Processing complete! You can now download your video.")
            with open(final_video, "rb") as f:
                video_bytes = f.read()
                st.video(video_bytes)
            with open(final_video, "rb") as f:
                st.download_button("📥 Download Final Video", f, file_name="final_output.mp4")
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
