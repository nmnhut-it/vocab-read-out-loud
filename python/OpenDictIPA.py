import json
from pathlib import Path
from typing import Optional, Dict, List, Union
import gzip
from collections import defaultdict

class OpenDictIPA:
    def __init__(self, data_dir: Union[str, Path]):
        """Initialize the IPA lookup using open-dict-data files.

        Args:
            data_dir: Directory containing the open-dict-data files
                     (e.g., 'en_US.txt.gz' for American English)
        """
        self.data_dir = Path(data_dir)
        self.pronunciations: Dict[str, List[str]] = defaultdict(list)
        self.loaded_varieties: List[str] = []

    def load_ipa_dict(self, variety: str = 'en_US'):
        """Load IPA pronunciations from ipa-dict data files.

        Args:
            variety: Language/variety code (e.g., 'en_US', 'en_GB')
        """
        file_path = self.data_dir / f"{variety}.txt"

        if not file_path.exists():
            raise FileNotFoundError(
                f"Could not find {variety} pronunciation data. "
                "Download it from https://github.com/open-dict-data/ipa-dict"
            )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        word, pron = line.strip().split('\t')
                        self.pronunciations[word.lower()].append(pron)

            self.loaded_varieties.append(variety)
        except Exception as e:
            raise RuntimeError(f"Error loading {variety} data: {str(e)}")

    def get_pronunciation(self, text: str) -> List[str]:
        """Get IPA pronunciation(s) for a word or phrase.

        Args:
            text: Word or phrase to look up

        Returns:
            List of IPA pronunciations. Empty list if not found.
        """
        text = text.lower()

        # Direct lookup for single words
        if text in self.pronunciations:
            return self.pronunciations[text]

        # Handle multi-word phrases
        words = text.split()
        if len(words) > 1:
            word_pronunciations = []
            for word in words:
                if word in self.pronunciations:
                    word_pronunciations.append(self.pronunciations[word][0])  # Take first pronunciation for each word
                else:
                    return []  # If any word is missing, return empty list
            return [' '.join(word_pronunciations)]  # Combine words with spaces

        return []  # Word not found

    def add_pronunciation(self, text: str, pronunciation: str):
        """Add or update a custom pronunciation.

        Args:
            text: Word or phrase to add
            pronunciation: IPA pronunciation to add
        """
        text = text.lower()
        if pronunciation not in self.pronunciations[text]:
            self.pronunciations[text].append(pronunciation)

    def export_pronunciations(self, output_file: Union[str, Path]):
        """Export pronunciations to a text file in the same format as input.

        Args:
            output_file: Path to save the pronunciations
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            for word, prons in sorted(self.pronunciations.items()):
                for pron in prons:
                    f.write(f"{word}\t{pron}\n")

    def import_pronunciations(self, input_file: Union[str, Path]):
        """Import pronunciations from a JSON file.

        Args:
            input_file: Path to the JSON file
        """
        input_file = Path(input_file)
        with input_file.open('r', encoding='utf-8') as f:
            imported_data = json.load(f)
            for word, prons in imported_data.items():
                self.pronunciations[word.lower()].extend(prons)

    def get_varieties(self) -> List[str]:
        """Get list of loaded language varieties."""
        return self.loaded_varieties.copy()