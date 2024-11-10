import os
from typing import List, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import TextClip, CompositeVideoClip, AudioFileClip, ColorClip
from moviepy.editor import ImageClip, concatenate_videoclips
from dataclasses import dataclass
from WordEntry import WordEntry
from FlashcardGenerator import FlashcardGenerator
from PIL.Image import Resampling  # Import the new Resampling enum

@dataclass
class ThemeColors:
    bg: str
    text: str
    accent: str
    secondary: str

class EnhancedFlashcardGenerator(FlashcardGenerator):
    def __init__(self):
        super().__init__()
        # Define professional color schemes
        self.themes = {
            'blue': ThemeColors(
                bg='#F0F4F8',
                text='#1A365D',
                accent='#2B6CB0',
                secondary='#4299E1'
            ),
            'green': ThemeColors(
                bg='#F0FDF4',
                text='#1C4532',
                accent='#2F855A',
                secondary='#48BB78'
            ),
            'red': ThemeColors(
                bg='#FFF5F5',
                text='#63171B',
                accent='#C53030',
                secondary='#F56565'
            ),
            'gray': ThemeColors(
                bg='#F7FAFC',
                text='#2D3748',
                accent='#4A5568',
                secondary='#A0AEC0'
            )
        }
        self.current_theme = self.themes['green']

    def set_theme(self, theme_name: str):
        """Set the current color theme"""
        if theme_name in self.themes:
            self.current_theme = self.themes[theme_name]
        else:
            raise ValueError(f"Theme '{theme_name}' not found. Available themes: {list(self.themes.keys())}")

    def create_intro_outro(self, duration: int = 1.0) -> Tuple[CompositeVideoClip, CompositeVideoClip]:
        """Create professional intro and outro sequences"""
        # Create background with gradient effect
        bg = ColorClip(size=(1280, 720), color=EnhancedFlashcardGenerator.hex_to_rgb(self.current_theme.accent))
        bg = bg.set_duration(duration)

        # Create intro text with animation
        intro_text = TextClip(
            txt="English Vocabulary\nFlashcards",
            fontsize=70,
            color='white',
            font='Arial-Bold',
            kerning=2,
            align='center'
        ).set_duration(duration)

        subtitle_text = TextClip(
            txt="Created by Nguyễn Minh Nhựt\nnmnhut.en@gmail.com\ngithub.com/nmnhut-it",
            fontsize=20,
            color='white',
            font='Arial',
            kerning=1
        ).set_duration(duration)

        # Position text clips
        intro_text = intro_text.set_position('center').crossfadein(0.5)
        subtitle_text = subtitle_text.set_position(('center', 500)).crossfadein(0.5)

        intro = CompositeVideoClip([bg, intro_text, subtitle_text])

        # Create outro with call-to-action
        outro_text = TextClip(
            txt="Thanks for watching!\n\nSubscribe for more!\n\n" +
                "Email: nmnhut.en@gmail.com\nGithub:github.com/nmnhut-it",
            fontsize=40,
            color='white',
            font='Arial',
            kerning=2,
            align='center'
        ).set_duration(duration)

        outro_text = outro_text.set_position('center').crossfadein(0.5)
        outro = CompositeVideoClip([bg, outro_text])

        return intro, outro

    def get_background_color(self):
        return self.current_theme.bg;
    def create_transition(self, duration: float = 0.5, style: str = 'slide') -> Union[ColorClip, CompositeVideoClip]:
        """
        Create smooth, eye-friendly transition effects

        Args:
            duration: Length of transition in seconds
            style: Transition style ('fade', 'slide', or 'zoom')

        Returns:
            MoviePy clip with transition effect
        """
        if style == 'fade':
            # Gentle fade to/from semi-transparent black
            transition = ColorClip(
                size=(1280, 720),
                color=EnhancedFlashcardGenerator.hex_to_rgb(self.current_theme.bg)
            ).set_opacity(0.3)
            # Create fade in/out effect with full opacity
            return (transition
                    .set_duration(duration)
                    .set_opacity(lambda t: 1 if t < duration/2 else 1 - 2*(t-duration/2)/duration))

        elif style == 'slide':
            # Sliding transition using two panels
            left_panel = ColorClip(
                size=(640, 720),
                color=EnhancedFlashcardGenerator.hex_to_rgb(self.current_theme.bg)
            )
            right_panel = ColorClip(
                size=(640, 720),
                color=EnhancedFlashcardGenerator.hex_to_rgb(self.current_theme.bg)
            )

            # Set positions with movement
            left_panel = (left_panel
                        .set_position(lambda t: (-(640 * t/duration), 0))
                        .set_duration(duration))
            right_panel = (right_panel
                        .set_position(lambda t: (1280 - (640 * t/duration), 0))
                        .set_duration(duration))

            return CompositeVideoClip([left_panel, right_panel])

        elif style == 'zoom':
            # Subtle zoom fade transition
            bg = ColorClip(
                size=(1280, 720),
                color=EnhancedFlashcardGenerator.hex_to_rgb(self.current_theme.bg)
            )
            bg = bg.set_duration(duration)

            # Add zoom effect
            bg = bg.resize(lambda t: 1 + 0.05 * t/duration)
            bg = bg.set_position('center')
            bg = bg.set_opacity(lambda t: 1 - t/duration)

            return bg

        else:
            # Default to simple crossfade if style not recognized
            return ColorClip(
                size=(1280, 720),
                color=EnhancedFlashcardGenerator.hex_to_rgb(self.current_theme.bg)
            ).set_duration(duration).crossfadein(0.4).crossfadeout(0.4)

    def create_progress_bar(self, current: int, total: int, duration: float) -> ColorClip:
        """Create animated progress bar using RGB colors"""
        # Convert hex colors to RGB tuples
        secondary_color = EnhancedFlashcardGenerator.hex_to_rgb(self.current_theme.secondary)
        accent_color = EnhancedFlashcardGenerator.hex_to_rgb(self.current_theme.accent)

        # Background bar
        bg_width = 700
        bg_height = 8
        bg_bar = ColorClip(
            size=(bg_width, bg_height),
            color=secondary_color
        ).set_opacity(0.3)

        # Progress bar
        progress_width = int(bg_width * (current / total))
        progress = ColorClip(
            size=(progress_width, bg_height),
            color=accent_color
        )

        # Combine bars
        composite = CompositeVideoClip([bg_bar, progress])
        composite = composite.set_position(('center', 180))
        return composite.set_duration(duration)

    def draw_text_with_shadow(self, draw: ImageDraw, position: Tuple[int, int],
                            text: str, font: ImageFont, color: str):
        """Draw text with subtle shadow effect"""
        x, y = position
        # Draw shadow
        shadow_offset = 2
        draw.text((x + shadow_offset, y + shadow_offset), text,
                 font=font, fill=self.adjust_color_brightness(color, -30), anchor="mm")
        # Draw main text
        draw.text((x, y), text, font=font, fill=color, anchor="mm")

    def draw_text_with_highlight(self, draw: ImageDraw, position: Tuple[int, int],
                               text: str, font: ImageFont, color: str, bg_color: str):
        """Draw text with background highlight effect"""
        x, y = position
        # Calculate text size
        bbox = draw.textbbox((x, y), text, font=font, anchor="mm")
        padding = 20

        # Draw highlight background
        highlight_color = self.adjust_color_brightness(bg_color, -5)
        draw.rectangle(
            (bbox[0] - padding, bbox[1] - padding/2,
             bbox[2] + padding, bbox[3] + padding/2),
            fill=highlight_color
        )

        # Draw text
        draw.text((x, y), text, font=font, fill=color, anchor="mm")

    def add_background_pattern(self, draw: ImageDraw, color: str):
        """Add subtle background pattern"""
        pattern_color = self.adjust_color_brightness(color, 10)
        spacing = 40
        opacity = 30

        for x in range(0, 1280, spacing):
            for y in range(0, 720, spacing):
                draw.ellipse(
                    [x-2, y-2, x+2, y+2],
                    fill=self.adjust_color_opacity(pattern_color, opacity)
                )

    def create_video(self, entries: List[WordEntry], include_intro: bool = True,
                background_music: Optional[str] = None) -> str:
        """
        Create enhanced video with proper image resampling.
        """
        clips = []
        temp_clips = []  # Track temporary clips for cleanup

        try:
            # Create base background with RGB tuple
            bg_color = EnhancedFlashcardGenerator.hex_to_rgb(self.current_theme.secondary)
            base_bg = ColorClip(
                size=(1280, 720),
                color=bg_color
            ).set_duration(1)
            print (base_bg);

            # Add intro if requested
            if include_intro:
                intro, outro = self.create_intro_outro()
                clips.append(intro)
                temp_clips.extend([intro])

            # Create transition clip
            # transition = self.create_transition()
            # temp_clips.append(transition)

            # Process each word entry
            total_entries = len(entries)
            for idx, entry in enumerate(entries, 1):
                try:
                    # Generate audio and image components
                    audio_path = self.generate_audio(entry.word)
                    image_path = self.create_card_image(entry)

                    # Load audio and calculate duration
                    audio_clip = AudioFileClip(audio_path)
                    clip_duration = audio_clip.duration + 1.5

                    # Create background for this clip
                    clip_bg = base_bg.set_duration(clip_duration)
                    print (clip_bg);

                    # Load image
                    pil_image = Image.open(image_path)
                    print ("load image from " + image_path)
                    # Calculate new dimensions while maintaining aspect ratio
                    target_width = 1280
                    ratio = target_width / pil_image.width
                    target_height = int(pil_image.height * ratio)

                    # Resize using LANCZOS resampling
                    pil_image = pil_image.resize(
                        (target_width, target_height),
                        resample=Resampling.LANCZOS
                    )

                    # Save resized image
                    resized_path = os.path.join(self.image_dir, f"resized_{os.path.basename(image_path)}")
                    pil_image.save(resized_path)

                    # Create movie clip from resized image
                    image_clip = (ImageClip(resized_path)
                                .set_duration(clip_duration)
                                .set_position('center'))

                    # Create progress bar
                    progress = self.create_progress_bar(idx, total_entries, clip_duration)

                    # Combine layers with background
                    video_clip = CompositeVideoClip(
                        [image_clip, progress],
                        size=(1280, 720)
                    )
                    video_clip = video_clip.set_audio(audio_clip)

                    # Add transition between cards
                    # if idx > 1:
                    #     clips.append(transition)
                    clips.append(video_clip)
                    print ("append to clips " + str(idx))

                    # Track for cleanup
                    temp_clips.extend([audio_clip, image_clip, progress, video_clip])

                    # Clean up resized image
                    try:
                        os.remove(resized_path)
                    except:
                        pass

                except Exception as e:
                    print(f"Warning: Error processing entry {entry.word}: {str(e)}")
                    continue

            # Add outro if intro was included
            if include_intro:
                # clips.append(transition)
                print("include outro")
                clips.append(outro)
                temp_clips.append(outro)

            if not clips:
                raise ValueError("No valid clips were created")

            # Concatenate all clips
            final_clip = concatenate_videoclips(clips, method="compose")
            temp_clips.append(final_clip)
            print("to final clip")

            # Add background music if provided
            if background_music and os.path.exists(background_music):
                try:
                    bg_music = AudioFileClip(background_music)
                    bg_music = bg_music.volumex(0.1).loop(duration=final_clip.duration)
                    final_with_music = CompositeVideoClip([final_clip])
                    final_with_music = final_with_music.set_audio(
                        CompositeVideoClip([final_clip, bg_music]).audio
                    )
                    temp_clips.extend([bg_music, final_with_music])
                    final_clip = final_with_music
                except Exception as e:
                    print(f"Warning: Could not add background music: {str(e)}")

            # Generate output path
            output_path = os.path.join(self.output_dir, f"flashcards_{self.timestamp}.mp4")

            # Write final video
            final_clip.write_videofile(
                output_path,
                fps=8,
                codec='libx264',
                audio_codec='aac',
                audio_bitrate='192k',
                threads=4,
                logger=None
            )
            print("finish writing")
            return output_path

        except Exception as e:
            raise RuntimeError(f"Error generating video: {str(e)}") from e

        finally:
            # Clean up all temporary clips
            for clip in temp_clips:
                try:
                    clip.close()
                except Exception:
                    pass

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple, ensuring numeric types"""
        hex_color = hex_color.lstrip('#')
        rgb = (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )
        print(f"Converting {hex_color} to RGB: {rgb}")  # Debug print
        return rgb;

    @staticmethod
    def adjust_color_brightness(hex_color: str, factor: int) -> str:
        """Adjust color brightness by a factor"""
        rgb = EnhancedFlashcardGenerator.hex_to_rgb(hex_color)
        new_rgb = tuple(
            min(255, max(0, value + factor))
            for value in rgb
        )
        return f'#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}'

    @staticmethod
    def adjust_color_opacity(hex_color: str, opacity: int) -> str:
        """Adjust color opacity (0-255)"""
        rgb = EnhancedFlashcardGenerator.hex_to_rgb(hex_color)
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}{opacity:02x}'