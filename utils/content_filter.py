"""Content filter and cleaner."""

import re

def load_blocked_phrases():
    """Load user's list of strings to block."""
    try:
        with open('config/blocked_phrases.txt', 'r') as file:
            return [line.strip().lower() for line in file if line.strip()]
    except FileNotFoundError:
        print("Warning: blocked_phrases.txt not found")
        return []

def contains_blocked_phrase(text: str, blocked_phrases: list) -> tuple[bool, str, str]:
    """Check if string contains a blocked substring, and filter it out if so."""
    text_lower = text.lower()
    for phrase in blocked_phrases:
        # Create a pattern that matches whole words only
        pattern = r'\b' + re.escape(phrase) + r'\b'
        if re.search(pattern, text_lower):
            # Find the sentence containing the blocked phrase
            sentences = text.split('.')
            for sentence in sentences:
                if re.search(pattern, sentence.lower()):
                    return True, sentence.strip(), phrase
    return False, "", ""
