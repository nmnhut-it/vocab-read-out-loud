import gradio as gr
from typing import Dict, Set, List
import re
import os
from datetime import datetime
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk.tag import pos_tag

class RootWordAnalyzer:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.all_previous_lemmas = set()

    def get_wordnet_pos(self, tagged_word: tuple) -> str:
        """Convert NLTK POS tag to WordNet POS tag"""
        _, tag = tagged_word
        tag_dict = {
            'JJ': wordnet.ADJ,
            'JJR': wordnet.ADJ,
            'JJS': wordnet.ADJ,
            'NN': wordnet.NOUN,
            'NNS': wordnet.NOUN,
            'NNP': wordnet.NOUN,
            'NNPS': wordnet.NOUN,
            'RB': wordnet.ADV,
            'RBR': wordnet.ADV,
            'RBS': wordnet.ADV,
            'VB': wordnet.VERB,
            'VBD': wordnet.VERB,
            'VBG': wordnet.VERB,
            'VBN': wordnet.VERB,
            'VBP': wordnet.VERB,
            'VBZ': wordnet.VERB,
        }
        return tag_dict.get(tag, wordnet.NOUN)

    def get_root_words(self, text: str) -> Set[str]:
        """Extract root forms of words from text."""
        # Tokenize and clean text
        words = word_tokenize(text.lower())

        # Only keep alphabetic words
        words = [word for word in words if word.isalpha()]

        # Tag words with POS
        tagged_words = pos_tag(words)

        # Get lemmas using POS tags
        lemmas = set()
        for tagged_word in tagged_words:
            pos = self.get_wordnet_pos(tagged_word)
            lemma = self.lemmatizer.lemmatize(tagged_word[0], pos)
            lemmas.add(lemma)

        return lemmas

    def extract_pages(self, text: str) -> List[tuple]:
        """Extract pages from text."""
        parts = re.split(r'={2,}\s*Page\s+(\d+)\s*={2,}', text)

        if parts[0].strip() == '':
            parts = parts[1:]

        pages = []
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                page_num = int(parts[i])
                content = parts[i + 1].strip()
                pages.append((page_num, content))

        return pages

    def analyze_pages(self, text: str) -> Dict[int, Set[str]]:
        """Analyze text and return new root words by page."""
        # Reset state
        self.all_previous_lemmas.clear()

        # Store results: page_num -> set of new root words
        page_analysis = {}

        # Process each page
        for page_num, content in self.extract_pages(text):
            # Get root words for this page
            current_roots = self.get_root_words(content)

            # Find new root words (not seen in previous pages)
            new_roots = current_roots - self.all_previous_lemmas

            # Store new roots
            if new_roots:
                page_analysis[page_num] = new_roots

            # Update seen roots
            self.all_previous_lemmas.update(current_roots)

        return page_analysis

    def format_results(self, analysis: Dict[int, Set[str]]) -> str:
        """Format the analysis results as text."""
        lines = []
        total_words = sum(len(roots) for roots in analysis.values())

        lines.append(f"Total unique root words: {total_words}")
        lines.append("=" * 50)

        for page_num in sorted(analysis.keys()):
            roots = sorted(analysis[page_num])

            lines.append(f"\nPage {page_num} - {len(roots)} new root words:")
            lines.append("-" * 50)

            # Show roots in columns
            for i in range(0, len(roots), 5):
                row = roots[i:i+5]
                lines.append("  ".join(word.ljust(15) for word in row))

        return "\n".join(lines)

    def save_results(self, text: str, output_dir: str = "results") -> tuple:
        """Analyze and save results to file."""
        os.makedirs(output_dir, exist_ok=True)

        # Analyze text
        analysis = self.analyze_pages(text)
        results = self.format_results(analysis)

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"root_words_{timestamp}.txt")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(results)

        return results, filename

def process_file(file_path: str, save_output: bool) -> str:
    """Process input file."""
    if not file_path:
        return "Please upload a file."

    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Analyze text
        analyzer = RootWordAnalyzer()
        if save_output:
            results, filepath = analyzer.save_results(text)
            return f"{results}\n\nResults saved to: {filepath}"
        else:
            analysis = analyzer.analyze_pages(text)
            return analyzer.format_results(analysis)

    except Exception as e:
        return f"Error processing file: {str(e)}"

def create_interface():
    with gr.Blocks(title="Root Word Analyzer") as interface:
        gr.Markdown("# Root Word Analyzer")
        gr.Markdown("""
        ## Instructions
        1. Upload a text file with pages marked as:
        ```
        ==================== Page 1 ====================
        Your text here
        ==================== Page 2 ====================
        More text here
        ```
        2. Click 'Analyze File' to see new root words in each page
        """)

        with gr.Row():
            with gr.Column(scale=2):
                file_input = gr.File(
                    label="Upload Text File (.txt)",
                    file_types=[".txt"]
                )
                save_checkbox = gr.Checkbox(
                    label="Save results to file",
                    value=True
                )
                analyze_button = gr.Button("Analyze File", variant="primary")

            with gr.Column(scale=2):
                output_text = gr.Textbox(
                    label="Analysis Results",
                    lines=15
                )

        analyze_button.click(
            fn=process_file,
            inputs=[file_input, save_checkbox],
            outputs=output_text
        )

        # Example file
        example = """==================== Page 1 ====================
He writes a book and runs fast.
==================== Page 2 ====================
She wrote many books and was running.
==================== Page 3 ====================
They write stories and will run tomorrow."""

        os.makedirs("examples", exist_ok=True)
        example_file = "examples/example.txt"
        with open(example_file, "w", encoding="utf-8") as f:
            f.write(example)

        gr.Examples(
            examples=[[example_file]],
            inputs=[file_input]
        )

    return interface


if __name__ == "__main__":
    # Download required NLTK data
    nltk.download('punkt_tab')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('averaged_perceptron_tagger_eng')
    nltk.download('wordnet')
    nltk.download('omw-1.4')

    # Launch interface
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False
    )