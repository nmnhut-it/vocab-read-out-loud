import gradio as gr
import os
from pathlib import Path
from OCRTool import OCRTool
import tempfile
from pdf2image import convert_from_path
import shutil

class GradioOCRInterface:
    def __init__(self):
        self.ocr_tool = OCRTool()

    def convert_pdf_to_images(self, pdf_path):
        """Convert PDF file to images"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, poppler_path="D:/poppler-24.08.0/Library/bin")
            return images
        except Exception as e:
            raise Exception(f"Failed to convert PDF: {str(e)}")

    def process_file(self, file, lang):
        """Process a single file (image or PDF) and return extracted text"""
        try:
            file_path = Path(file.name)

            # Handle PDF files
            if file_path.suffix.lower() == '.pdf':
                images = self.convert_pdf_to_images(file_path)
                texts = []
                for i, image in enumerate(images, 1):
                    # Save the image temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                        image.save(temp_file.name)
                        # Extract text using OCR tool
                        text = self.ocr_tool.extract_text(temp_file.name, lang)
                        texts.append(f"Page {i}:\n{text}")
                    os.unlink(temp_file.name)
                return "\n\n" + "="*50 + "\n\n".join(texts)

            # Handle image files
            else:
                text = self.ocr_tool.extract_text(file_path, lang)
                return text if not text.startswith("Error:") else f"❌ {text}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def process_image(self, image, lang):
        """Process a single uploaded image and return extracted text"""
        try:
            # Save the image temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                image.save(temp_file.name)
                # Extract text using OCR tool
                text = self.ocr_tool.extract_text(temp_file.name, lang)
            # Clean up temporary file
            os.unlink(temp_file.name)

            return text if not text.startswith("Error:") else f"❌ {text}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def process_batch(self, files, lang):
        """Process multiple files (images or PDFs) and return results"""
        results = []
        for file in files:
            try:
                file_path = Path(file.name)
                filename = file_path.name

                # Handle PDF files
                if file_path.suffix.lower() == '.pdf':
                    results.append(f"📑 Processing PDF: {filename}")
                    images = self.convert_pdf_to_images(file_path)
                    for i, image in enumerate(images, 1):
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                            image.save(temp_file.name)
                            text = self.ocr_tool.extract_text(temp_file.name, lang)
                            results.append(f"Page {i}:\n{text}")
                        os.unlink(temp_file.name)

                # Handle image files
                else:
                    text = self.ocr_tool.extract_text(file_path, lang)
                    results.append(f"📄 {filename}:\n{text}")

                results.append("="*50)

            except Exception as e:
                results.append(f"❌ Error processing {filename}: {str(e)}")
                results.append("="*50)

        return "\n\n".join(results)

    def create_interface(self):
        """Create and configure the Gradio interface"""
        # Available language options
        languages = {
            "English": "eng",
            "French": "fra",
            "German": "deu",
            "Spanish": "spa",
            "Italian": "ita"
        }

        # Create interface with tabs for single and batch processing
        with gr.Blocks(title="OCR Text Extraction Tool") as interface:
            gr.Markdown("# OCR Text Extraction Tool")
            gr.Markdown("Extract text from images and PDFs using Tesseract OCR")

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
                            lines=10
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
                            lines=15
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