import re

def escape_markdown(text: str) -> str:
    if not isinstance(text, str):
        return text
    return re.sub(r'([*_`])', r'\\\\\\1', text)