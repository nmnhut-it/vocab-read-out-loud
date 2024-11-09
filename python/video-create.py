import gradio as gr
import re
from dataclasses import dataclass
from typing import List, Optional
from gtts import gTTS
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
from moviepy.editor import ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import os
import tempfile
import shutil
import os
from datetime import datetime
from OpenDictIPA import OpenDictIPA;
import unicodedata


@dataclass
class WordEntry:
    word: str
    word_type: Optional[str]
    meaning: str
    pronunciation: Optional[str] = None
    number: Optional[int] = None
    irregular_forms: List[str] = None

# Modify your WordParser class:
class WordParser:
    def __init__(self, ipa_lookup: Optional[OpenDictIPA] = None):
        self.ipa_lookup = ipa_lookup

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
            word = irregular_forms[0]
            # If no pronunciation provided in input, try to look it up
            if not pronunciation and self.ipa_lookup:
                pronunciations = self.ipa_lookup.get_pronunciation(word)
                if pronunciations:
                    # Use first pronunciation
                    pronunciation = pronunciations[0]
        else:
            word = word_part
            # If no pronunciation provided in input, try to look it up
            if not pronunciation and self.ipa_lookup:
                pronunciations = self.ipa_lookup.get_pronunciation(word)
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


    def normalize_pronunciation(self, ipa_text: str) -> str:
        ipa_text = unicodedata.normalize("NFC",ipa_text);
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

class FlashcardGenerator:
    def __init__(self):
        # Create output directories if they don't exist
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"flashcards_{self.timestamp}"
        self.audio_dir = os.path.join(self.output_dir, "audio")
        self.image_dir = os.path.join(self.output_dir, "images")

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

    def create_card_image(self, entry: WordEntry,
                     word_size: int = 72,
                     type_size: int = 48,
                     pron_size: int = 48,
                     meaning_size: int = 56) -> str:
        """
        Create a flashcard image with customizable font sizes

        Args:
            entry: WordEntry containing word information
            word_size: Font size for the main word (default: 72)
            type_size: Font size for word type (default: 48)
            pron_size: Font size for pronunciation (default: 48)
            meaning_size: Font size for meaning (default: 56)

        Returns:
            str: Path to the generated image file
        """
        img = Image.new('RGB', (1280, 720), color='white')
        draw = ImageDraw.Draw(img)

        # Load Times New Roman font in different sizes
        try:
            word_font = ImageFont.truetype("times.ttf", word_size)
            type_font = ImageFont.truetype("times.ttf", type_size)
            pron_font = ImageFont.truetype("times.ttf", pron_size)
            meaning_font = ImageFont.truetype("times.ttf", meaning_size)
            watermark_font = ImageFont.truetype("times.ttf", meaning_size/2)
        except OSError:
            # Fallback to Arial or system default if Times New Roman is not available
            try:
                word_font = ImageFont.truetype("arial.ttf", word_size)
                type_font = ImageFont.truetype("arial.ttf", type_size)
                pron_font = ImageFont.truetype("arial.ttf", pron_size)
                meaning_font = ImageFont.truetype("arial.ttf", meaning_size)
                watermark_font = ImageFont.truetype("arial.ttf", meaning_size/2)
            except OSError:
                # If no system fonts are available, use default
                print("Warning: Could not load custom fonts. Using default font.")
                word_font = ImageFont.load_default()
                type_font = ImageFont.load_default()
                pron_font = ImageFont.load_default()
                meaning_font = ImageFont.load_default()
                watermark_font = ImageFont.load_default()


        # Define positions with more space for larger text
        word_y = 180
        type_y = word_y + 100
        pron_y = type_y + 100
        meaning_y = pron_y + 100
        watermark_y = meaning_y + 100
        center_x = 640

        # Draw word (and irregular forms if present)
        word_text = entry.word
        if entry.irregular_forms:
            word_text = " - ".join(entry.irregular_forms)

        # Draw elements with custom fonts
        draw.text((center_x, word_y), word_text,
                font=word_font, fill='black', anchor="mm")

        if entry.word_type:
            draw.text((center_x, type_y), f"({entry.word_type})",
                    font=type_font, fill='gray', anchor="mm")

        if entry.pronunciation:
            draw.text((center_x, pron_y), f"/{entry.pronunciation}/",
                    font=pron_font, fill='blue', anchor="mm")

        draw.text((center_x, meaning_y), entry.meaning,
                font=meaning_font, fill='black', anchor="mm")

        #
        draw.text((center_x, watermark_y), "Created by: Nguyễn Minh Nhựt - nmnhut.en@gmail.com",
                font=watermark_font, fill='grey', anchor="mm")


        # Save image with safe filename
        safe_word = "".join(c if c.isalnum() else "_" for c in entry.word)
        img_path = os.path.join(self.image_dir, f"{safe_word}.png")
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
        output_path = os.path.join(self.output_dir, "flashcards.mp4")

        try:
            final_clip.write_videofile(output_path, fps=24, codec='libx264')
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

def process_text(text: str) -> str:
    """Process input text and generate video"""
    # Initialize the IPA lookup
    ipa_lookup = OpenDictIPA(".")
    ipa_lookup.load_ipa_dict("en_UK")  # Load American English pronunciations
    parser = WordParser(ipa_lookup=ipa_lookup);
    generator = FlashcardGenerator()

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

# Create Gradio interface
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
            generate_btn = gr.Button("Generate Video")

        with gr.Row():
            video_output = gr.Video(label="Generated Flashcards")

        generate_btn.click(
            fn=process_text,
            inputs=[text_input],
            outputs=[video_output]
        )

    return app

# initialize



#---------------------------------------------------

if __name__ == "__main__":
    app = create_interface()
    app.launch()