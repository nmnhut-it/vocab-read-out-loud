import os
import sys
import pytesseract
from PIL import Image
import argparse
import logging
from pathlib import Path
from OCRTool import OCRTool

def test_installation():
    """Test Tesseract installation and print version info"""
    try:
        version = pytesseract.get_tesseract_version()
        print(f"Tesseract version: {version}")
        return True
    except Exception as e:
        print(f"Tesseract installation test failed: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Extract text from images using OCR')
    parser.add_argument('input', help='Image file or directory path')
    parser.add_argument('--lang', default='eng', help='OCR language (default: eng)')
    parser.add_argument('--test', action='store_true', help='Test Tesseract installation')
    args = parser.parse_args()

    if args.test:
        test_installation()
        return

    try:
        ocr = OCRTool()

        input_path = Path(args.input)

        if input_path.is_file():
            # Process single file
            text = ocr.extract_text(str(input_path), args.lang)
            if not text.startswith("Error:"):
                print(f"\nExtracted text from {input_path.name}:")
                print("-" * 50)
                print(text)
                print("-" * 50)
            else:
                print(f"\nError processing {input_path.name}:")
                print(text)

        elif input_path.is_dir():
            # Process directory
            results = ocr.extract_from_directory(str(input_path))
            for filename, text in results.items():
                if not text.startswith("Error:"):
                    print(f"\nFile: {filename}")
                    print("-" * 50)
                    print(text)
                    print("-" * 50)
                else:
                    print(f"\nError processing {filename}:")
                    print(text)

        else:
            print(f"Error: '{args.input}' is not a valid file or directory")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()