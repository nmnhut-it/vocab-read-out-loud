import gradio as gr
import re
from dataclasses import dataclass
from typing import List, Optional,Tuple, List, Dict
from gtts import gTTS
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
from moviepy.editor import ImageClip, concatenate_videoclips
from moviepy.config import change_settings

from PIL import Image, ImageDraw, ImageFont
import os
import tempfile
import shutil
import os
from datetime import datetime
from OpenDictIPA import OpenDictIPA;
import unicodedata
import pandas as pd

from IPAFontManager import IPAFontManager
from WordEntry import WordEntry;

# Configure MoviePy to use ImageMagick
def configure_moviepy():
    """Configure MoviePy with ImageMagick path"""
    # Try to find ImageMagick in common installation paths
    possible_paths = [
        r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
        r"C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe",
        r"C:\Program Files (x86)\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
        r"C:\Program Files (x86)\ImageMagick-7.1.1-Q16\magick.exe"
    ]

    # Search for magick.exe in Program Files
    program_files = os.environ.get('PROGRAMFILES', r'C:\Program Files')
    for root, dirs, files in os.walk(program_files):
        if 'magick.exe' in files:
            possible_paths.append(os.path.join(root, 'magick.exe'))

    # Try each path
    for path in possible_paths:
        if os.path.exists(path):
            change_settings({"IMAGEMAGICK_BINARY": path})
            print(f"ImageMagick found at: {path}")
            return True

    raise RuntimeError(
        "ImageMagick not found. Please install ImageMagick and ensure it's in your system PATH.\n"
        "Download from: https://imagemagick.org/script/download.php#windows"
    )

# Modify your WordParser class:
class WordParser:
    def __init__(self, ipa_lookup: Optional[OpenDictIPA] = None):
        self.ipa_uk_lookup = ipa_lookup
        self.ipa_us_lookup = ipa_lookup


    def parse_line(self, line: str, line_number: int = None) -> WordEntry:
        """Parse a single line of the word list"""
        line = line.strip()

        # Pattern for line with pronunciation at end
        pattern1 = r'^(?:(\d+)\.\s+)?([^:]+):\s*(?:\(([a-z]+)\))?\s*([^/]+)(?:/([^/]+)/)?\s*$'

        match = re.match(pattern1, line)
        if not match:
            raise ValueError(f"Invalid line format: {line}")

        number = int(match.group(1)) if match.group(1) else line_number
        word_part = match.group(2).strip()
        word_type = match.group(3)
        meaning = match.group(4).strip()
        pronunciation = match.group(5).strip() if match.group(5) else None



        # Check for irregular verb forms
        irregular_forms = None
        if " - " in word_part:
            irregular_forms = [form.strip() for form in word_part.split(" - ")]
            combined_pronunciation = None;
            word = word_part
            if (pronunciation is None):
                for word in irregular_forms:
                    # If no pronunciation provided in input, try to look it up
                    if not pronunciation and self.ipa_uk_lookup:
                        pronunciations = self.get_pronunciation(word)
                        if pronunciations:
                            # Use first pronunciation
                            pronunciation = pronunciations[0]
                            pronunciation = self.normalize_pronunciation(pronunciation);
                    if not combined_pronunciation:
                        combined_pronunciation = pronunciation;
                    else:
                        combined_pronunciation = combined_pronunciation +"-"+ pronunciation
                    print (pronunciation);
                    pronunciation = None

                if combined_pronunciation is not None:
                    pronunciation = combined_pronunciation;

        else:
            word = word_part
            # If no pronunciation provided in input, try to look it up
            if not pronunciation and self.ipa_uk_lookup:
                pronunciations = self.get_pronunciation(word)
                if pronunciations:
                    pronunciation = pronunciations[0]
                    pronunciation = self.normalize_pronunciation(pronunciation);
        return WordEntry(
            number=number,
            word=word,
            word_type=word_type,
            meaning=meaning,
            pronunciation=pronunciation,
            irregular_forms=irregular_forms
        )

    def get_pronunciation(self,word):
        first = self.ipa_uk_lookup.get_pronunciation(word);
        if len(first) > 0:
            return first;
        return first;


    def normalize_pronunciation(self, ipa_text: str) -> str:
        ipa_text = unicodedata.normalize("NFC",ipa_text).strip("/").strip("/");
        """
        Normalize stress marks to the standard IPA vertical line.
        """
        # Different possible stress mark characters
        stress_marks = {
            '\u02C8',  # ˈ MODIFIER LETTER VERTICAL LINE (preferred IPA)
            '\u0027',  # ' APOSTROPHE
            '\u2032',  # ′ PRIME
        }
        # Replace all variants with the standard IPA stress mark
        for mark in stress_marks:
            ipa_text = ipa_text.replace(mark, 'ˈ')  # Using standard IPA stress mark

        ipa_text = ipa_text.replace('ɫ','l')

        return ipa_text
    def parse_text(self, text: str) -> List[WordEntry]:
        """Parse the entire text input"""
        lines = [line for line in text.strip().split("\n") if line.strip()]
        entries = []

        for i, line in enumerate(lines, 1):
            try:
                entry = self.parse_line(line, i)
                entries.append(entry)
            except ValueError as e:
                print(f"Warning: Skipping invalid line {i}: {e}")

        return entries


from EnhancedFlashcardGenerator import EnhancedFlashcardGenerator

def process_text(text: str) -> str:
    """Process input text and generate video"""
    # Initialize the IPA lookup
    ipa_lookup = OpenDictIPA(".")
    ipa_lookup.load_ipa_dict("en_UK")  # Load American English pronunciations
    ipa_lookup.load_ipa_dict("en_US")  # Load American English pronunciations
    parser = WordParser(ipa_lookup=ipa_lookup);

    generator = EnhancedFlashcardGenerator()

    try:
        entries = parser.parse_text(text)
        if not entries:
            raise ValueError("No valid entries found in the input text")
        video_path = generator.create_video(entries)
        return video_path
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        raise
    finally:
        generator.cleanup()

import gradio as gr
from typing import Tuple

def format_word_entry(entry) -> str:
    """Format a single word entry to standardized format"""
    parts = []

    # Handle irregular forms
    if entry.irregular_forms:
        parts.append(" - ".join(entry.irregular_forms))
    else:
        parts.append(entry.word)

    # Add word type if exists
    if entry.word_type:
        parts.append(f"({entry.word_type})")

    # Add meaning
    parts.append(entry.meaning)

    # Add pronunciation if exists
    if entry.pronunciation:
        parts.append(f"/{entry.pronunciation}/")

    return ": ".join(parts[:2]) + " " + " ".join(parts[2:])

def parse_and_preview(text: str) -> Tuple[str, str]:
    """
    Parse text and return standardized format
    Returns formatted text and status message
    """
    if not text.strip():
        return "", "Please enter some text to process"

    try:
        # Initialize the IPA lookup
        ipa_lookup = OpenDictIPA(".")
        ipa_lookup.load_ipa_dict("en_UK")
        ipa_lookup.load_ipa_dict("en_US")
        parser = WordParser(ipa_lookup=ipa_lookup)

        # Parse entries
        entries = parser.parse_text(text)
        if not entries:
            return "", "No valid entries found in the input text"

        # Format entries to standardized text
        formatted_lines = []
        for i, entry in enumerate(entries, 1):
            formatted_line = f"{i}. {format_word_entry(entry)}"
            formatted_lines.append(formatted_line)

        formatted_text = "\n".join(formatted_lines)
        return (
            formatted_text,
            f"Found {len(entries)} words. Review the formatted text below and make any needed changes before creating the video."
        )
    except Exception as e:
        return "", f"Error processing text: {str(e)}"

def create_interface():
    with gr.Blocks() as app:
        gr.Markdown("""
        # English Flashcard Video Generator

        Enter your word list in either format:
        ```
        1. design: (v) thiết kế
        2. buy - bought - bought: (v) mua

        # Or without numbers:
        rainforest: (n) rừng mưa nhiệt đới /ˈreɪnfɒrɪst/
        climate change: biến đổi khí hậu /ˈklaɪmət tʃeɪndʒ/
        ```
        """)

        with gr.Row():
            text_input = gr.Textbox(
                label="Enter word list",
                lines=10,
                placeholder="Enter your word list here..."
            )

        with gr.Row():
            parse_btn = gr.Button("Format Text")
            generate_btn = gr.Button("Create Video")

        # Status message
        status_msg = gr.Markdown("")

        with gr.Row():
            preview_text = gr.Textbox(
                label="Formatted Word List (edit if needed)",
                lines=10,
                placeholder="Processed text will appear here..."
            )

        with gr.Row():
            video_output = gr.Video(
                label="Generated Flashcards",
                height=360,
                width=640
            )

        def start_video_generation(text):
            if not text:
                return None, "Please format the word list first before creating video."
            try:
                video_path = process_text(text)
                return video_path, "Video generation complete!"
            except Exception as e:
                return None, f"Error generating video: {str(e)}"

        # Parse and preview handling
        parse_btn.click(
            fn=parse_and_preview,
            inputs=[text_input],
            outputs=[preview_text, status_msg]
        )

        # Video generation handling
        generate_btn.click(
            fn=start_video_generation,
            inputs=[preview_text],
            outputs=[video_output, status_msg]
        )

        # Reset interface when text input changes
        def reset_interface():
            return "", "Input changed. Click 'Format Text' to update."

        text_input.change(
            fn=reset_interface,
            outputs=[preview_text, status_msg]
        )

    return app

if __name__ == "__main__":
    configure_moviepy()
    app = create_interface()
    app.launch()