import os
import sys
import pytesseract
from PIL import Image
import argparse
import logging
from pathlib import Path
import shutil

class OCRTool:
    def __init__(self, tesseract_path=None):
        """Initialize OCR tool with platform-aware Tesseract path detection"""
        self.tesseract_path = self._get_tesseract_path(tesseract_path)

        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

        # Set up logging
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def _get_tesseract_path(self, custom_path=None):
        """
        Determine the Tesseract executable path based on the platform
        Returns None if Tesseract is in system PATH
        """
        if custom_path and os.path.exists(custom_path):
            return custom_path

        # Check if tesseract is in system PATH
        tesseract_cmd = 'tesseract.exe' if sys.platform == 'win32' else 'tesseract'
        if shutil.which(tesseract_cmd):
            return None  # Let pytesseract use system PATH

        # Common installation paths
        possible_paths = []
        if sys.platform == 'win32':
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
            ]
        elif sys.platform == 'darwin':  # macOS
            possible_paths = [
                '/usr/local/bin/tesseract',
                '/opt/homebrew/bin/tesseract'
            ]
        else:  # Linux
            possible_paths = [
                '/usr/bin/tesseract',
                '/usr/local/bin/tesseract'
            ]

        # Return the first valid path or raise an error
        for path in possible_paths:
            if os.path.exists(path):
                return path

        raise FileNotFoundError(
            "Tesseract not found. Please ensure it's installed and either:\n"
            "1. Added to your system PATH, or\n"
            "2. Specify the path manually when creating OCRTool instance"
        )

    def preprocess_image(self, image_path):
        """Preprocess image for better OCR results"""
        try:
            # Open image with Pillow
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('L', 'RGB'):
                    img = img.convert('RGB')

                # Return a copy of the processed image
                return img.copy()
        except Exception as e:
            self.logger.error(f"Error preprocessing {image_path}: {str(e)}")
            raise

    def extract_text(self, image_path, lang='eng'):
        """Extract text from an image with robust error handling"""
        try:
            # Verify file exists and is a file
            path = Path(image_path)
            if not path.is_file():
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Check file extension
            if path.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                raise ValueError(f"Unsupported file format: {path.suffix}")

            # Preprocess the image
            img = self.preprocess_image(image_path)

            # Configure OCR parameters for better results
            custom_config = r'--oem 3 --psm 3'

            # Perform OCR
            text = pytesseract.image_to_string(img, lang=lang, config=custom_config)

            # Clean up the text
            text = text.strip()

            self.logger.info(f"Successfully processed {image_path}")
            return text

        except Exception as e:
            self.logger.error(f"Error processing {image_path}: {str(e)}")
            return f"Error: {str(e)}"

    def extract_from_directory(self, directory, extensions=None):
        """Extract text from all images in a directory"""
        if extensions is None:
            extensions = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']

        directory_path = Path(directory)
        if not directory_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {directory}")

        results = {}
        for ext in extensions:
            for file_path in directory_path.glob(f"*{ext}"):
                try:
                    text = self.extract_text(str(file_path))
                    results[file_path.name] = text
                except Exception as e:
                    results[file_path.name] = f"Error: {str(e)}"
                    self.logger.error(f"Failed to process {file_path}: {str(e)}")

        return results