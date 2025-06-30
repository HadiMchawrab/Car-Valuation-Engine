# File: scraper/utils.py

import re
from collections import OrderedDict
from rapidfuzz import fuzz
import pandas as pd  # for loading master-list from Excel

# -----------------------------
# Configuration
# -----------------------------

EN_STOPWORDS = [
    r'for sale', r'used', r'excellent', r'engine', r'subcompact',
    r'mileage', r'fleet', r'luxury', r'in very', r'its up for',
    r'and', r'the', r'buy', r'new', r'pls', r'in', r'car',
    r'for', r'usb', r'abs', r'led', r'its', r'has', r'very',
    r'suv', r'black', r'are', r'one', r'is', r'cvt', r'all', 
    r'any', r'won', r'odo', r'rwd', r'awd', r'not', r'rpm', 
    r'can', r'may', r'red', r'blue', r'gcc', r'fwd', r'aux', 
    r'ago', r'v8', r'bmw', r'mph' , r'gas', r'www', r'sar', 
    r'aed', r'with', r'use', r'due', r'kmh', r'kms', r'key', 
    r'non', r'you', r'yea', r'was' , r'hot', r'got', r'have',
    r'our', r'bad', r'oil', r'bag'
]
EN_STOPWORDS_RE = re.compile(
    r'\b(' + r'|'.join([re.escape(w) for w in EN_STOPWORDS]) + r')\b',
    flags=re.IGNORECASE
)
YEAR_RE = re.compile(r'\b(19|20)\d{2}\b')

# Patterns for “edition” and 3-letter tokens
EDITION_RE = re.compile(r'\b(\w+)\s+edition\b', re.IGNORECASE)
TRI_RE     = re.compile(r'\b([A-Za-z]{3})\b')

# -----------------------------
# Script Detection & Normalization
# -----------------------------

def is_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

def normalize_en(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = YEAR_RE.sub(' ', text)
    text = EN_STOPWORDS_RE.sub(' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def normalize_ar(text: str) -> str:
    text = re.sub(r'[\u064B-\u0652\u0640]', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'[ؤئ]', 'ء', text)
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'[^\u0600-\u06FF\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def normalize_text(text: str) -> str:
    """
    Auto-select Arabic or English normalization. Returns ''
    for empty or whitespace-only input.
    """
    if not text or not text.strip():
        return ''
    return normalize_ar(text) if is_arabic(text) else normalize_en(text)


# -----------------------------
# Master-list loading & matching
# -----------------------------

def load_master_trims(
    file_path: str,
    sheet_name=0,
    column: str = 'trim'
) -> list[str]:
    """
    Read an Excel sheet column of high-confidence trims.
    Returns a list of normalized, deduplicated phrases.
    """
    df = pd.read_csv(file_path, usecols=[column])
    phrases = df[column].dropna().astype(str).unique()
    return [normalize_text(p) for p in phrases if normalize_text(p)]

def extract_master_trims(text: str, master_list: list[str]) -> list[str]:
    """
    Return any master-list phrase that appears (normalized) in the text.
    """
    norm = normalize_text(text)
    return [phrase for phrase in master_list if phrase in norm]


# -----------------------------
# Helper: Strip make/model
# -----------------------------

def strip_make_model(text: str, make: str, model: str) -> str:
    pattern = re.compile(
        rf'\b(?:{re.escape(make)}|{re.escape(model)})\b',
        flags=re.IGNORECASE
    )
    return re.sub(r'\s+', ' ', pattern.sub('', text)).strip()


# -----------------------------
# Candidate Extraction
# -----------------------------

def extract_candidates(
    text: str,
    make: str,
    model: str,
    max_words: int = 1
) -> list[str]:
    """
    Find "<Make> <Model>" in text, then grab up to `max_words` tokens
    immediately following. Strip any stray make/model terms.
    """
    words = text.split()
    pattern = re.compile(
        rf"{re.escape(make)}\s+{re.escape(model)}\b",
        flags=re.IGNORECASE
    )
    cands = []
    for i in range(len(words)):
        window = " ".join(words[i : i + 2])
        if pattern.match(window):
            phrase = " ".join(words[i + 2 : i + 2 + max_words]).strip()
            if phrase:
                cleaned = strip_make_model(phrase, make, model)
                if cleaned:
                    cands.append(cleaned)
    return cands

def extract_pre_edition(text: str) -> list[str]:
    """Capture words immediately before 'Edition'."""
    return [m.group(1) for m in EDITION_RE.finditer(text)]

def extract_three_letter(text: str) -> list[str]:
    """Capture standalone 3-letter English tokens (e.g. GLX, SEI)."""
    return TRI_RE.findall(text)


# -----------------------------
# Fuzzy Clustering & Mapping
# -----------------------------

def fuzzy_cluster(variants: list[str], threshold: int = 80) -> OrderedDict:
    """
    Cluster normalized variant strings into an OrderedDict:
      seed_string → [members...]
    Uses token_set_ratio for matching.
    """
    clusters = OrderedDict()
    for v in variants:
        placed = False
        for seed in clusters:
            if fuzz.token_set_ratio(v, seed) >= threshold:
                clusters[seed].append(v)
                placed = True
                break
        if not placed:
            clusters[v] = [v]
    return clusters

def map_to_cluster(
    value: str,
    clusters: dict,
    threshold: int = 80
) -> str:
    """
    Map a normalized string to the best cluster seed (if score ≥ threshold),
    otherwise return the value itself.
    """
    best_key, best_score = None, 0
    for seed in clusters:
        score = fuzz.token_set_ratio(value, seed)
        if score > best_score:
            best_key, best_score = seed, score
    return best_key if best_score >= threshold else value
