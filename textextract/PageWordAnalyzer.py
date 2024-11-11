import gradio as gr
from typing import Dict, Set, List, Tuple
from collections import defaultdict
import re
import os
from datetime import datetime

class PageWordAnalyzer:
    def __init__(self):
        self.all_previous_words = set()
        self.words_per_page = defaultdict(set)

    def clean_text(self, text: str) -> List[str]:
        """Clean text and split into words."""
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        return [word for word in text.split() if word]

    def extract_page_content(self, text: str) -> List[Tuple[int, str]]:
        """Extract page numbers and content from text with === Page X === format."""
        # Split text by the page marker pattern
        parts = re.split(r'={2,}\s*Page\s+(\d+)\s*={2,}', text)

        # First part is empty if text starts with a page marker
        if parts[0].strip() == '':
            parts = parts[1:]

        # Process parts in pairs (page number and content)
        pages = []
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                page_num = int(parts[i])
                content = parts[i + 1].strip()
                pages.append((page_num, content))

        return pages

    def analyze_pages(self, text: str) -> Dict[int, Set[str]]:
        """Analyze text with multiple pages and return new unique words per page."""
        # Reset state for new analysis
        self.all_previous_words.clear()
        self.words_per_page.clear()

        # Extract pages and their content
        pages = self.extract_page_content(text)

        # Process each page
        for page_num, content in pages:
            current_page_words = set(self.clean_text(content))
            new_words = current_page_words - self.all_previous_words
            self.words_per_page[page_num] = new_words
            self.all_previous_words.update(current_page_words)

        return dict(self.words_per_page)

    def format_results(self, include_word_count: bool = True) -> str:
        """Format analysis results as a string."""
        output_lines = []
        total_unique_words = 0

        for page_num in sorted(self.words_per_page.keys()):
            words = sorted(self.words_per_page[page_num])
            total_unique_words += len(words)

            output_lines.append(f"\nPage {page_num} - {len(words)} new unique words:")
            output_lines.append("-" * 50)

            # Format words in columns
            for i in range(0, len(words), 5):
                row = words[i:i+5]
                output_lines.append("  ".join(word.ljust(15) for word in row))

        if include_word_count:
            output_lines.insert(0, f"Total number of unique words across all pages: {total_unique_words}")
            output_lines.insert(1, "=" * 50)

        return "\n".join(output_lines)

    def save_results(self, text: str, output_dir: str = "results") -> Tuple[str, str]:
        """Analyze text and save results to a file."""
        # Create results directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Analyze the text
        self.analyze_pages(text)

        # Generate formatted results
        results_text = self.format_results()

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"word_analysis_{timestamp}.txt")

        # Save to file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(results_text)

        return results_text, filename

def process_input(file_path: str, save_output: bool) -> str:
    """Process input file and optionally save results."""
    # Check if file was provided
    if not file_path:
        return "Please upload a file."

    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Process the text
        analyzer = PageWordAnalyzer()
        if save_output:
            results, filepath = analyzer.save_results(text)
            return f"{results}\n\nResults saved to: {filepath}"
        else:
            analyzer.analyze_pages(text)
            return analyzer.format_results()

    except Exception as e:
        return f"Error processing file: {str(e)}"

# Create Gradio interface
def create_interface():
    with gr.Blocks(title="Page Word Analyzer") as interface:
        gr.Markdown("# Page Word Analyzer")
        gr.Markdown("""
        ## Instructions
        1. Upload a text file containing pages in the format:
        ```
        ==================== Page 1 ====================
        Your text here
        ==================== Page 2 ====================
        More text here
        ```
        2. Click 'Analyze File' to process the text
        3. Results will show unique words for each page (excluding words from previous pages)
        """)

        with gr.Row():
            with gr.Column(scale=2):
                # File input
                file_input = gr.File(
                    label="Upload Text File (.txt)",
                    file_types=[".txt"]
                )
                save_checkbox = gr.Checkbox(
                    label="Save results to file (saved in 'results' directory)",
                    value=True
                )
                process_button = gr.Button("Analyze File", variant="primary")

            with gr.Column(scale=2):
                output_text = gr.Textbox(
                    label="Analysis Results",
                    lines=15
                )

        # Set up event handler
        process_button.click(
            fn=process_input,
            inputs=[file_input, save_checkbox],
            outputs=output_text
        )

        # Add example file
        example_text = """==================== Page 1 ====================
The cat and dog played in the yard.
==================== Page 2 ====================
The cat played with a ball while the bird watched.
==================== Page 3 ====================
A new butterfly joined the bird in the garden."""

        # Create example file
        os.makedirs("examples", exist_ok=True)
        example_file = "examples/example.txt"
        with open(example_file, "w", encoding="utf-8") as f:
            f.write(example_text)

        gr.Examples(
            examples=[[example_file]],
            inputs=[file_input]
        )

    return interface

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )