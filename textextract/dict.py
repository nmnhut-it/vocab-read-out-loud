import gradio as gr
import nltk
import re
from collections import defaultdict
from pathlib import Path
import pystardict
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import os
import traceback

# Download required NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')

def get_wordnet_pos(tag):
    """Map NLTK part of speech tag to WordNet POS tag"""
    tag_dict = {
        'N': wordnet.NOUN,
        'V': wordnet.VERB,
        'R': wordnet.ADV,
        'J': wordnet.ADJ
    }
    return tag_dict.get(tag[0], wordnet.NOUN)

def pos_to_simple(pos_tag):
    """Convert WordNet POS to simple format"""
    pos_map = {
        'N': 'n',
        'V': 'v',
        'R': 'adv',
        'J': 'adj'
    }
    return pos_map.get(pos_tag[0], '')

def standardize_content(content):
    """
    Standardize text content by cleaning special characters and formatting
    """
    # Normalize line endings to \n
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # Character replacements dictionary
    replacements = {
        # Quotes and apostrophes
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '´': "'",
        '`': "'",

        # Dashes and hyphens
        '—': '-',  # em dash
        '–': '-',  # en dash
        '‐': '-',  # hyphen
        '‑': '-',  # non-breaking hyphen

        # Ellipsis
        '…': '...',

        # Spaces
        '\u00A0': ' ',  # non-breaking space
        '\t': ' ',      # tabs to spaces

        # Accented characters
        'é': 'e',
        'è': 'e',
        'ê': 'e',
        'ë': 'e',
        'á': 'a',
        'à': 'a',
        'â': 'a',
        'ä': 'a',
        'í': 'i',
        'ì': 'i',
        'î': 'i',
        'ï': 'i',
        'ó': 'o',
        'ò': 'o',
        'ô': 'o',
        'ö': 'o',
        'ú': 'u',
        'ù': 'u',
        'û': 'u',
        'ü': 'u',
        'ý': 'y',
        'ÿ': 'y',
        'ñ': 'n',
    }

    # Replace special characters
    for old, new in replacements.items():
        content = content.replace(old, new)

    # Split into lines and process
    lines = content.split('\n')
    processed_lines = []
    current_page = 0
    needs_page_marker = True

    for line in lines:
        # Clean the line
        line = line.strip()

        # Skip empty lines between page markers
        if not line:
            continue

        # Check if it's a page marker
        page_marker_match = re.search(r'={2,}\s*Page\s+(\d+)\s*={2,}', line)

        if page_marker_match:
            current_page = int(page_marker_match.group(1))
            # Standardize page marker format
            line = f"==================== Page {current_page} ===================="
            needs_page_marker = False
        elif needs_page_marker:
            # Add page marker if missing
            current_page += 1
            processed_lines.append(f"==================== Page {current_page} ====================")
            needs_page_marker = False

        processed_lines.append(line)

    # Join lines with proper spacing and ensure Unix-style line endings
    content = '\n\n'.join(processed_lines)

    # Clean up multiple newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content

def standardize_text_file(input_file, output_file=None):
    """
    Standardize a text file by:
    1. Converting special characters to ASCII
    2. Ensuring proper page markers format
    3. Cleaning up extra whitespace and empty lines
    4. Ensuring UTF-8 encoding and Unix-style line endings
    """
    try:
        # Determine output file path
        if output_file is None:
            file_path = Path(input_file)
            output_file = str(file_path.parent / f"{file_path.stem}_standardized{file_path.suffix}")

        # Read content in binary mode to handle line endings
        with open(input_file, 'rb') as f:
            content_bytes = f.read()

        # Try different encodings
        encodings = ['utf-8', 'utf-16', 'windows-1252', 'iso-8859-1']
        content = None

        for encoding in encodings:
            try:
                content = content_bytes.decode(encoding)
                print(f"Successfully read file with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            # Last resort: decode with utf-8 and ignore errors
            content = content_bytes.decode('utf-8', errors='ignore')

        # Clean the content
        cleaned_content = standardize_content(content)

        # Write standardized content with Unix line endings
        with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
            f.write(cleaned_content)

        print(f"Standardized file saved to: {output_file}")
        return output_file

    except Exception as e:
        print(f"Error standardizing file: {str(e)}")
        raise

def create_example_file(filename="example.txt"):
    """Create an example text file with multiple pages"""
    content = """==================== Page 1 ====================
The book is on the table. I write every day and run in the morning.

==================== Page 2 ====================
There are many books on many shelves. I'm writing a story.

==================== Page 3 ====================
The story continues as I write more chapters in my book."""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

class WordAnalyzer:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.seen_words = set()
        self.dict_lookup = None
    def load_dictionary(self, dict_path):
        """Load StarDict dictionary files including compressed .dict.dz"""
        try:
            base_path = dict_path.rstrip('/')  # Remove trailing slash if exists
            base_name = base_path.rsplit('/', 1)[-1]  # Get base name

            # Check for required files
            required_files = {
                'idx': f"{base_path}/{base_name}.idx",
                'ifo': f"{base_path}/{base_name}.ifo",
            }

            # Check for either .dict or .dict.dz
            dict_file = f"{base_path}/{base_name}.dict"
            dict_dz_file = f"{base_path}/{base_name}.dict.dz"

            if os.path.exists(dict_dz_file):
                required_files['dict'] = dict_dz_file
            elif os.path.exists(dict_file):
                required_files['dict'] = dict_file
            else:
                return False, f"Dictionary file not found. Looked for:\n{dict_file}\n{dict_dz_file}"

            # Verify all required files exist
            missing_files = [f for f, path in required_files.items() if not os.path.exists(path)]
            if missing_files:
                return False, f"Missing files: {', '.join(missing_files)}\nPaths checked:\n" + \
                    "\n".join(f"{k}: {v}" for k, v in required_files.items())

            # Create stardict object with correct paths
            self.dict_lookup = pystardict.Dictionary(base_path + '/' + base_name)

            # Test dictionary access
            try:
                # Try to look up a common word to verify dictionary works
                test_word = "the"
                self.dict_lookup[test_word]
                return True, "Dictionary loaded successfully"
            except Exception as e:
                return False, f"Dictionary loaded but test lookup failed: {str(e)}"

        except Exception as e:
            return False, f"Error loading dictionary: {str(e)}"

    def process_text(self, text_content):
        """Process text and extract words page by page"""
        if not self.dict_lookup:
            return "Please load a dictionary first."

        pages = re.split(r'==================== Page \d+ ====================', text_content)
        pages = [p.strip() for p in pages if p.strip()]

        results = []
        total_words = 0

        for i, page_content in enumerate(pages, 1):
            page_words = defaultdict(set)

            # Tokenize and process words
            tokens = word_tokenize(page_content.lower())
            pos_tags = nltk.pos_tag(tokens)

            for word, pos in pos_tags:
                if not word.isalpha():
                    continue

                wordnet_pos = get_wordnet_pos(pos)
                lemma = self.lemmatizer.lemmatize(word, wordnet_pos)

                if lemma not in self.seen_words:
                    simple_pos = pos_to_simple(pos)
                    if simple_pos:  # Only add words with valid POS
                        page_words[lemma].add(simple_pos)

            # Process new words found on this page
            new_words = []
            for word in page_words:
                if word not in self.seen_words:
                    self.seen_words.add(word)
                    try:
                        dict_entry = self.dict_lookup[word]
                        for pos in sorted(page_words[word]):
                            new_words.append(f"{word} ({pos}): {dict_entry}")
                    except KeyError:
                        new_words.append(f"{word} ({', '.join(page_words[word])}): <not found in dictionary>")

            if new_words:
                results.append(f"Page {i} - {len(new_words)} new words:")
                results.extend(sorted(new_words))
                total_words += len(new_words)

        output = f"Total unique root words: {total_words}\n"
        output += "=====================================\n"
        output += "\n".join(results)

        return output

def analyze_text(text_file, dict_path, save_output=False):
    """Main function to analyze text and handle the Gradio interface"""
    try:
        if text_file is None:
            return "Please upload a text file."

        # First standardize the file
        try:
            standardized_file = standardize_text_file(text_file.name)
        except Exception as e:
            return f"Error standardizing file: {str(e)}"

        analyzer = WordAnalyzer()
        dict_success, dict_message = analyzer.load_dictionary(dict_path)
        if not dict_success:
            return dict_message

        # Read from standardized file
        with open(standardized_file, 'r', encoding='utf-8') as f:
            text_content = f.read()

        results = analyzer.process_text(text_content)

        if save_output and results:
            output_file = "analysis_results.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(results)
            results += f"\n\nResults saved to {output_file}"

        return results
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return f"Error processing text: {str(e)}"

def create_interface():
    """Create the Gradio interface"""
    iface = gr.Interface(
        fn=analyze_text,
        inputs=[
            gr.File(label="Upload Text File (.txt)", file_types=[".txt"]),
            gr.Textbox(label="StarDict Dictionary Path (path to .dict/.idx/.ifo files)",
                      value="D:/AnhViet/stardict_en_vi/"),
            gr.Checkbox(label="Save results to file")
        ],
        outputs=gr.Textbox(label="Analysis Results", lines=20),
        title="Page-by-Page Word Analyzer with StarDict",
        description="""
        This tool analyzes text files page by page and extracts new words with their Vietnamese translations and IPA.
        Pages should be separated by '==================== Page X ====================' markers.
        """,
        examples=[
            [create_example_file(), "D:/AnhViet/stardict_en_vi/", False]
        ]
    )
    return iface

if __name__ == "__main__":
    interface = create_interface()
    interface.launch()