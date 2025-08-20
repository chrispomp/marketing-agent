import hashlib
import re

def slugify(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    if len(text) <= max_len:
        return text
    h = hashlib.sha1(text.encode()).hexdigest()[:6]
    return f"{text[:max_len-7]}-{h}"
