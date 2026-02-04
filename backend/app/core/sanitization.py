import re
from typing import Optional

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|above|prior)",
    r"forget\s+(everything|all)\s+(above|you\s+know)",
    r"new\s+instructions?\s*:",
    r"system\s*:\s*",
    r"assistant\s*:\s*",
    r"user\s*:\s*",
    r"<\|.*?\|>",
    r"\[INST\].*?\[/INST\]",
    r"```\s*(system|prompt)",
    r"you\s+are\s+now\s+in\s+",
    r"act\s+as\s+if\s+you\s+are",
    r"pretend\s+(that\s+)?you\s+are",
    r"from\s+now\s+on\s*,?\s*(you\s+are|ignore)",
    r"override\s+(your\s+)?instructions",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

MAX_CONTEXT_LENGTH = 5000


def sanitize_for_prompt(
    text: Optional[str],
    max_length: int = MAX_CONTEXT_LENGTH,
    field_name: str = "input",
) -> str:
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    sanitized = text

    for pattern in COMPILED_PATTERNS:
        sanitized = pattern.sub("[REMOVED]", sanitized)

    sanitized = sanitized.replace("{{", "{ {").replace("}}", "} }")

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... [truncated]"

    return sanitized


def sanitize_url(url: Optional[str]) -> str:
    if url is None:
        return ""

    if not isinstance(url, str):
        return ""

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        return ""

    if len(url) > 2000:
        return ""

    dangerous_patterns = [
        r"javascript:",
        r"data:",
        r"vbscript:",
        r"file:",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return ""

    return url
