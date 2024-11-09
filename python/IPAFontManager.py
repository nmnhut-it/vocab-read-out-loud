import os
import platform
import requests
from pathlib import Path
from typing import Dict
from PIL import ImageFont

class IPAFontManager:
    def __init__(self, fonts_dir: str = './fonts'):
        """
        Initialize font manager with automatic Noto Sans font download capability.

        Args:
            fonts_dir: Directory to store fonts (default: './fonts')
        """
        self.fonts_dir = Path(fonts_dir)
        self.fonts_dir.mkdir(exist_ok=True)

        # Check both possible filenames for Noto Sans
        self.font_files = ['NotoSans-Regular.ttf', 'Noto_Sans-Regular.ttf']
        self.font_source = {
            'url': 'https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf',
            'filename': 'NotoSans-Regular.ttf'
        }

        # System-specific font paths
        self.system_font_paths = self._get_system_font_paths()

    def _get_system_font_paths(self) -> Dict[str, Path]:
        """Get system-specific font paths based on OS."""
        system = platform.system().lower()

        if system == 'windows':
            return {
                'system': Path('C:/Windows/Fonts'),
                'user': Path(os.path.expanduser('~/AppData/Local/Microsoft/Windows/Fonts'))
            }
        elif system == 'darwin':  # macOS
            return {
                'system': Path('/Library/Fonts'),
                'user': Path(os.path.expanduser('~/Library/Fonts'))
            }
        else:  # Linux and others
            return {
                'system': Path('/usr/share/fonts'),
                'user': Path(os.path.expanduser('~/.local/share/fonts'))
            }

    def _find_font_in_dir(self) -> Path | None:
        """
        Check if Noto Sans font exists in fonts directory.

        Returns:
            Path to the font file if found, None otherwise
        """
        for filename in self.font_files:
            font_path = self.fonts_dir / filename
            if font_path.exists():
                return font_path
        return None

    def _download_font(self) -> bool:
        """
        Download Noto Sans font if not present.

        Returns:
            bool: True if download successful, False otherwise
        """
        font_path = self.fonts_dir / self.font_source['filename']

        try:
            response = requests.get(self.font_source['url'], stream=True)
            response.raise_for_status()

            with open(font_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True

        except Exception as e:
            print(f"Error downloading font: {e}")
            return False

    def get_ipa_font(self, size: int = 48) -> ImageFont.FreeTypeFont:
        """
        Get Noto Sans font that correctly handles IPA characters.

        Args:
            size: Font size in points

        Returns:
            PIL ImageFont object

        Raises:
            RuntimeError if font cannot be found or downloaded
        """
        # Check project directory first
        font_path = self._find_font_in_dir()
        if font_path:
            try:
                return ImageFont.truetype(str(font_path), size)
            except OSError:
                print(f"Error loading existing font: {font_path}")

        # Try downloading if not found
        if self._download_font():
            font_path = self.fonts_dir / self.font_source['filename']
            try:
                return ImageFont.truetype(str(font_path), size)
            except OSError:
                print("Error loading downloaded font")

        # Try system fonts as last resort
        for font_dir in self.system_font_paths.values():
            if font_dir.exists():
                for font_file in font_dir.rglob('*.[Tt][Tt][Ff]'):
                    if 'noto' in font_file.name.lower():
                        try:
                            return ImageFont.truetype(str(font_file), size)
                        except OSError:
                            continue

        raise RuntimeError(
            "No Noto Sans font found and unable to download. "
            "Please check your internet connection or manually install Noto Sans."
        )

# Example usage
def test_font_manager():
    """Test the font manager functionality"""
    font_manager = IPAFontManager()

    try:
        font = font_manager.get_ipa_font(size=48)
        print("Successfully loaded Noto Sans font")

        # Create a test image
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (800, 200), 'white')
        draw = ImageDraw.Draw(img)

        test_text = "/dɪzˈaɪn/, /ˈæp.əl/, /ˈwɔː.tə/"
        draw.text((20, 20), test_text, font=font, fill='black')

        img.save("ipa_test.png")
        print("Test image saved as 'ipa_test.png'")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_font_manager()