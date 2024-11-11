import os
import sys
import pytesseract
from PIL import Image
import logging
from pathlib import Path
import re

class OCRTool:
    def __init__(self, tesseract_path=r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        """Initialize OCR tool with Tesseract path"""
        if not os.path.exists(tesseract_path):
            raise FileNotFoundError(f"Tesseract not found at: {tesseract_path}")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Set up logging
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def preprocess_image(self, image_path):
        """Preprocess image for better OCR results"""
        try:
            # Open and convert image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('L', 'RGB'):
                    img = img.convert('RGB')

                # Return a copy of the processed image
                return img.copy()
        except Exception as e:
            self.logger.error(f"Error preprocessing {image_path}: {str(e)}")
            raise

    def format_text(self, text):
        """Format extracted text while preserving meaningful spaces"""
        # Define patterns for form fields
        form_patterns = [
            (r'_{2,}', lambda m: '_' * len(m.group())),  # Preserve multiple underscores
            (r'\.{3,}', lambda m: '.' * len(m.group())), # Preserve multiple dots
            (r'(\s{3,})', lambda m: ' _____ '),          # Convert long spaces to underscores
            (r'□|\[\s*\]', '[ ]'),                       # Standardize checkboxes
            (r'■|\[x\]', '[x]'),                         # Standardize checked boxes
        ]

        # Split into lines while preserving empty lines
        lines = text.splitlines()
        formatted_lines = []

        for line in lines:
            # Preserve lines that are just form fields
            if re.match(r'^[\s_\.]+$', line):
                formatted_lines.append(line)
                continue

            # Process normal text lines
            processed_line = line.strip()

            # Apply form field patterns
            for pattern, replacement in form_patterns:
                if callable(replacement):
                    processed_line = re.sub(pattern, replacement, processed_line)
                else:
                    processed_line = re.sub(pattern, replacement, processed_line)

            # Add spacing around form fields
            processed_line = re.sub(r'(\S)(_+)(\S)', r'\1 \2 \3', processed_line)
            processed_line = re.sub(r'(\S)(\.{3,})(\S)', r'\1 \2 \3', processed_line)

            if processed_line:
                formatted_lines.append(processed_line)

        # Join lines and clean up
        text = '\n'.join(formatted_lines)

        # Fix hyphenation
        text = re.sub(r'([a-z])-\s*\n([a-z])', r'\1\2', text)

        # Normalize spacing while preserving form fields
        text = re.sub(r'(?<![_\.\s])\s{2,}(?![_\.\s])', ' ', text)

        # Ensure consistent paragraph breaks
        text = re.sub(r'\n\n+', '\n\n', text)

        return text.strip()

    def extract_text(self, image_path, lang='eng'):
        """Extract and format text from an image"""
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
            custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'

            # Perform OCR
            text = pytesseract.image_to_string(img, lang=lang, config=custom_config)

            # Format the text
            text = self.format_text(text)

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