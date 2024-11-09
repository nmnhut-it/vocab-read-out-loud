import gradio as gr
import re
from dataclasses import dataclass
from typing import List, Optional,Tuple, List, Dict
from gtts import gTTS
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
from moviepy.editor import ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Resampling  # Import the new Resampling enum

import os
import tempfile
import shutil
import os
from datetime import datetime
from OpenDictIPA import OpenDictIPA;
import unicodedata
import pandas as pd
from WordEntry import WordEntry;


from IPAFontManager import IPAFontManager
class FlashcardGenerator:
    def __init__(self):
        # Create output directories if they don't exist
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"flashcards_{self.timestamp}"
        self.audio_dir = os.path.join(self.output_dir, "audio")
        self.image_dir = os.path.join(self.output_dir, "images")
        self.font_manager = IPAFontManager()


        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

    def generate_audio(self, word: str) -> str:
        """Generate audio file for a word"""
        # Create safe filename
        safe_word = "".join(c if c.isalnum() else "_" for c in word)
        audio_path = os.path.join(self.audio_dir, f"{safe_word}.mp3")
        tts = gTTS(text=word, lang='en',tld="co.uk")
        tts.save(audio_path)
        return audio_path

    def get_background_color(self):
        return "white";

    def create_card_image(self, entry: WordEntry,
                        word_size: int = 72,
                        type_size: int = 48,
                        pron_size: int = 48,
                        meaning_size: int = 56,
                        background_path = "bg.jpg") -> str:
        # Load and resize background image
        if os.path.exists(background_path):
            background = Image.open(background_path)
            background = background.convert('RGB')
            background = background.resize((1280, 720), Image.Resampling.LANCZOS)
        else:
            # Fallback to solid color if background image not found
            background = Image.new('RGB', (1280, 720), color=self.get_background_color())

        img = background;
        # Create drawing object
        draw = ImageDraw.Draw(img)

        try:
            # Load fonts with error handling
            fonts = {
                'word': ImageFont.truetype("times.ttf", word_size),
                'type': ImageFont.truetype("times.ttf", type_size),
                'pron': self.font_manager.get_ipa_font(pron_size),
                'meaning': ImageFont.truetype("times.ttf", meaning_size),
                'watermark': ImageFont.truetype("times.ttf", meaning_size//2.3)
            }
        except OSError:
            try:
                # Fallback to Arial
                fonts = {
                    'word': ImageFont.truetype("arial.ttf", word_size),
                    'type': ImageFont.truetype("arial.ttf", type_size),
                    'pron': self.font_manager.get_ipa_font(pron_size),
                    'meaning': ImageFont.truetype("arial.ttf", meaning_size),
                    'watermark': ImageFont.truetype("arial.ttf", meaning_size//2.3)
                }
            except OSError:
                # Last resort fallback to default font
                print("Warning: Using default font as fallback")
                default_font = ImageFont.load_default()
                fonts = {k: default_font for k in ['word', 'type', 'pron', 'meaning', 'watermark']}

        # Define vertical positions
        positions = {
            'word': 220,
            'type': 300,
            'pron': 380,
            'meaning': 480,
            'watermark': 570
        }
        center_x = 640

        # Draw word (and irregular forms if present)
        word_text = entry.word
        if entry.irregular_forms:
            word_text = " - ".join(entry.irregular_forms)

        # Draw each element with error handling for text rendering
        try:
            draw.text((center_x, positions['word']), word_text,
                    font=fonts['word'], fill='black', anchor="mm")

            if entry.word_type:
                draw.text((center_x, positions['type']), f"({entry.word_type})",
                        font=fonts['type'], fill='gray', anchor="mm")

            if entry.pronunciation:
                draw.text((center_x, positions['pron']), f"/{entry.pronunciation}/",
                        font=fonts['pron'], fill='blue', anchor="mm")

            draw.text((center_x, positions['meaning']), entry.meaning,
                    font=fonts['meaning'], fill='black', anchor="mm")

            # Draw watermark
            watermark_text = "Created by Nguyễn Minh Nhựt - background designed by brgfx / Freepik"
            draw.text((center_x, positions['watermark']), watermark_text,
                    font=fonts['watermark'], fill='grey', anchor="mm")
        except Exception as e:
            print(f"Warning: Error drawing text: {str(e)}")
            # Continue with basic rendering if advanced text features fail
            draw.text((center_x, positions['word']), word_text,
                    font=ImageFont.load_default(), fill='black')

        # Save image with safe filename
        safe_word = "".join(c if c.isalnum() else "_" for c in entry.word)
        img_path = os.path.join(self.image_dir, f"{safe_word}.png")

        # Use LANCZOS resampling if resizing is needed
        if img.size != (1280, 720):
            img = img.resize((1280, 720), Resampling.LANCZOS)

        img.save(img_path)
        return img_path


    def create_video(self, entries: List[WordEntry]) -> str:
        """Create video from word entries"""
        clips = []

        for entry in entries:
            try:
                # Generate components
                audio_path = self.generate_audio(entry.word)
                image_path = self.create_card_image(entry)

                # Create clips
                audio_clip = AudioFileClip(audio_path)
                image_clip = ImageClip(image_path).set_duration(audio_clip.duration + 2)

                # Add audio to image clip
                video_clip = image_clip.set_audio(audio_clip)
                clips.append(video_clip)

            except Exception as e:
                print(f"Error processing entry {entry.word}: {str(e)}")
                continue

        if not clips:
            raise ValueError("No valid clips were created")

        # Concatenate all clips
        final_clip = concatenate_videoclips(clips, method="compose")
        output_path = os.path.join(self.output_dir, f"flashcards_{self.timestamp}.mp4")

        try:
            final_clip.write_videofile(output_path, fps=8, codec='libx264')
            return output_path
        finally:
            final_clip.close()
            for clip in clips:
                clip.close()

    def cleanup(self):
        """Clean up temporary files and clips"""
        try:
            shutil.rmtree(self.image_dir)
            shutil.rmtree(self.audio_dir)
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")