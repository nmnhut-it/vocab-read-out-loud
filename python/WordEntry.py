from dataclasses import dataclass
from typing import List, Optional,List
import os


@dataclass
class WordEntry:
    word: str
    word_type: Optional[str]
    meaning: str
    pronunciation: Optional[str] = None
    number: Optional[int] = None
    irregular_forms: List[str] = None