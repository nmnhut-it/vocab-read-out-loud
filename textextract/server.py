import gradio as gr
import os
from pathlib import Path
from OCRTool import OCRTool
import tempfile
from pdf2image import convert_from_path
import datetime
import json
from PIL import Image

class GradioOCRInterface:
    def __init__(self):
        self.ocr_tool = OCRTool()
        self.output_dir = Path("ocr_output")
        self.output_dir.mkdir(exist_ok=True)

        # Create metadata file
        self.metadata_file = self.output_dir / "processing_history.json"
        self.load_processing_history()

    def load_processing_history(self):
        """Load or initialize processing history"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.processing_history = json.load(f)
        else:
            self.processing_history = []

    def save_processing_history(self):
        """Save processing history to metadata file"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.processing_history, f, indent=2)

    def generate_output_filename(self, original_filename, batch=False):
        """Generate unique output filename"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(original_filename).stem
        if batch:
            return f"{stem}_batch_{timestamp}.txt"
        return f"{stem}_{timestamp}.txt"

    def save_text_output(self, text, original_filename, lang, batch=False):
        """Save extracted text to file and update history"""
        try:
            output_filename = self.generate_output_filename(original_filename, batch)
            output_path = self.output_dir / output_filename

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "original_file": original_filename,
                "output_file": output_filename,
                "language": lang,
                "batch_process": batch
            }
            self.processing_history.append(entry)
            self.save_processing_history()

            return str(output_path)
        except Exception as e:
            return f"Error saving output: {str(e)}"

    def convert_pdf_to_images(self, pdf_path, poppler_path=None):
        """Convert PDF file to images"""
        try:
            # Convert PDF to images with higher DPI for better quality
            images = convert_from_path(
                pdf_path,
                poppler_path=poppler_path,
                dpi=300,  # Higher DPI for better quality
                fmt='PNG'
            )
            return images
        except Exception as e:
            raise Exception(f"Failed to convert PDF: {str(e)}")

    def process_file(self, file, lang):
        """Process a single file and save output"""
        try:
            file_path = Path(file.name)

            # Handle PDF files
            if file_path.suffix.lower() == '.pdf':
                images = self.convert_pdf_to_images(file_path,poppler_path="D:/poppler-24.08.0/Library/bin")
                texts = []

                for i, image in enumerate(images, 1):
                    # Save the image temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                        image.save(temp_file.name)
                        # Extract text using OCR tool
                        text = self.ocr_tool.extract_text(temp_file.name, lang)
                        texts.append(f"\n{'='*20} Page {i} {'='*20}\n\n{text}")
                    os.unlink(temp_file.name)

                text = "\n\n".join(texts)

            else:
                # Handle image files
                text = self.ocr_tool.extract_text(file_path, lang)

            if not text.startswith("Error:"):
                # Save the output
                output_path = self.save_text_output(text, file_path.name, lang)
                return f"{text}\n\n[Output saved to: {output_path}]"
            else:
                return f"❌ {text}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def process_batch(self, files, lang):
        """Process multiple files and save combined output"""
        results = []
        combined_text = []

        for file in files:
            try:
                file_path = Path(file.name)
                filename = file_path.name

                # Add file header
                file_header = f"\n{'#'*40}\n{filename}\n{'#'*40}\n"
                results.append(file_header)
                combined_text.append(file_header)

                # Process file
                text = self.process_file(file, lang)
                # Remove the individual file save message for combined output
                text_for_combined = text.split("\n\n[Output saved to:")[0]

                results.append(text)
                combined_text.append(text_for_combined)

            except Exception as e:
                error_msg = f"❌ Error processing {filename}: {str(e)}"
                results.append(error_msg)
                combined_text.append(error_msg)

            separator = "\n" + "="*50 + "\n"
            results.append(separator)
            combined_text.append(separator)

        # Save combined output
        combined_output = "\n".join(combined_text)
        batch_output_path = self.save_text_output(
            combined_output,
            "batch_processing",
            lang,
            batch=True
        )

        # Add batch save message
        results.append(f"\n[Combined batch output saved to: {batch_output_path}]")

        return "\n".join(results)

    def create_interface(self):
        """Create and configure the Gradio interface"""
        languages = {
            "English": "eng",
            "French": "fra",
            "German": "deu",
            "Spanish": "spa",
            "Italian": "ita",
            "Chinese (Simplified)": "chi_sim",
            "Japanese": "jpn",
            "Korean": "kor"
        }

        with gr.Blocks(title="OCR Text Extraction Tool") as interface:
            gr.Markdown("# OCR Text Extraction Tool")
            gr.Markdown("""
            Extract text from images and PDFs with automatic saving to 'ocr_output' folder.
            Supports multiple languages and batch processing.
            """)

            with gr.Tabs():
                # Single file processing tab
                with gr.Tab("Single File"):
                    with gr.Row():
                        with gr.Column():
                            file_input = gr.File(
                                label="Upload Image or PDF",
                                file_types=[".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
                            )
                            single_lang = gr.Dropdown(
                                choices=list(languages.keys()),
                                value="English",
                                label="Select Language"
                            )
                            single_button = gr.Button("Extract Text", variant="primary")

                        single_output = gr.Textbox(
                            label="Extracted Text",
                            placeholder="Extracted text will appear here...",
                            lines=15
                        )

                # Batch processing tab
                with gr.Tab("Batch Processing"):
                    with gr.Row():
                        with gr.Column():
                            batch_files = gr.File(
                                file_count="multiple",
                                label="Upload Multiple Files (Images and/or PDFs)",
                                file_types=[".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
                            )
                            batch_lang = gr.Dropdown(
                                choices=list(languages.keys()),
                                value="English",
                                label="Select Language"
                            )
                            batch_button = gr.Button("Process All Files", variant="primary")

                        batch_output = gr.Textbox(
                            label="Batch Results",
                            placeholder="Results will appear here...",
                            lines=20
                        )

            # Set up event handlers
            single_button.click(
                fn=lambda file, lang: self.process_file(file, languages[lang]),
                inputs=[file_input, single_lang],
                outputs=single_output
            )

            batch_button.click(
                fn=lambda files, lang: self.process_batch(files, languages[lang]),
                inputs=[batch_files, batch_lang],
                outputs=batch_output
            )

        return interface

def main():
    # Create and launch the interface
    ocr_interface = GradioOCRInterface()
    interface = ocr_interface.create_interface()
    interface.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860,
    )

if __name__ == "__main__":
    main()