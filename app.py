# Voiceover Video Tool - GitHub Ready Version

# Description:
# This Python tool lets you take a video and a timestamped script to auto-generate a voiceover
# and export the final video with synced narration.
#
# ✅ Accepts script in the format:
# [0:00 - 0:05]
# "Text to narrate."

import os
import re
from moviepy.editor import VideoFileClip, AudioFileClip
from pydub import AudioSegment
from gtts import gTTS
import streamlit as st
import tempfile

def parse_script(script_text):
    blocks = re.findall(r"\[(.*?)\]\n\"(.*?)\"", script_text, re.DOTALL)
    script_entries = []
    for block in blocks:
        times, text = block
        start_str, end_str = times.strip().split(" - ")
        script_entries.append((start_str.strip(), end_str.strip(), text.strip()))
    return script_entries

def time_to_seconds(t):
    minutes, seconds = map(float, t.split(':'))
    return int(minutes * 60 + seconds)

def generate_voice_clip(text, lang='en'):
    tts = gTTS(text=text, lang=lang)
    filename = f"tmp_{hash(text)}.mp3"
    tts.save(filename)
    clip = AudioSegment.from_file(filename)
    os.remove(filename)
    return clip

def create_voiceover_audio(script_entries):
    audio = AudioSegment.silent(duration=0)
    for start, end, text in script_entries:
        start_ms = time_to_seconds(start) * 1000
        end_ms = time_to_seconds(end) * 1000
        target_duration = end_ms - start_ms
        voice_clip = generate_voice_clip(text)
        if len(voice_clip) < target_duration:
            voice_clip += AudioSegment.silent(duration=target_duration - len(voice_clip))
        else:
            voice_clip = voice_clip[:target_duration]
        pad_duration = start_ms - len(audio)
        if pad_duration > 0:
            audio += AudioSegment.silent(duration=pad_duration)
        audio += voice_clip
    return audio

def combine_video_audio(video_path, audio_path, output_path):
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    video = video.set_audio(audio)
    video.write_videofile(output_path, codec='libx264', audio_codec='aac')

# Streamlit app interface
st.title("🎙️ Video Voiceover Generator")
st.write("Upload a video and a timestamped script. We'll add an AI-generated voiceover for you!")

uploaded_video = st.file_uploader("Upload your video (mp4)", type=["mp4"])
uploaded_script = st.text_area("Paste your script (timestamped)", height=300)

if st.button("Generate Voiceover") and uploaded_video and uploaded_script:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(uploaded_video.read())
        video_path = tmp_video.name

    entries = parse_script(uploaded_script)
    voice_audio = create_voiceover_audio(entries)

    audio_path = tempfile.mktemp(suffix=".mp3")
    voice_audio.export(audio_path, format="mp3")

    output_path = tempfile.mktemp(suffix=".mp4")
    combine_video_audio(video_path, audio_path, output_path)

    st.success("✅ Voiceover added! Download your video below:")
    with open(output_path, "rb") as f:
        st.download_button("📥 Download Final Video", f, file_name="final_output.mp4")
