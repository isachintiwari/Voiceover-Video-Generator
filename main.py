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

def parse_script(script_text):
    """Parses timestamped script into a list of (start, end, text) tuples."""
    blocks = re.findall(r"\[(.*?)\]\n\"(.*?)\"", script_text, re.DOTALL)
    script_entries = []
    for block in blocks:
        times, text = block
        start_str, end_str = times.strip().split(" - ")
        script_entries.append((start_str.strip(), end_str.strip(), text.strip()))
    return script_entries

def time_to_seconds(t):
    """Convert MM:SS string to total seconds."""
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
    """Generate voiceover audio aligned to the script timestamps."""
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

def combine_video_audio(video_path, audio_output_path, final_output_path):
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_output_path)
    video = video.set_audio(audio)
    video.write_videofile(final_output_path, codec='libx264', audio_codec='aac')

# Example usage (replace these paths with your files):
"""
with open("script.txt") as f:
    script_text = f.read()

entries = parse_script(script_text)
audio = create_voiceover_audio(entries)
audio.export("voiceover_output.mp3", format="mp3")
combine_video_audio("input_video.mp4", "voiceover_output.mp3", "final_output.mp4")
"""

# To convert into a web app, use Streamlit:
# streamlit run app.py
