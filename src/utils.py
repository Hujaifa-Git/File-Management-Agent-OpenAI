import os
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
client = OpenAI()

from config import ALLOWED_EXTENSIONS, MAX_FILE_READ_BYTES, DEFAULT_CHUNK_SIZE, SAFE_BASE_DIR, summarization_model

def safe_path(path: str) -> str:
    """Resolve and ensure path is inside SAFE_BASE_DIR to avoid reading outside allowed scope."""
    abs_path = os.path.abspath(path)
    base = os.path.abspath(SAFE_BASE_DIR)
    if not abs_path.startswith(base):
        raise PermissionError(f"Access to path not allowed: {path}. Must be under {base}")
    return abs_path

def allowed_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def get_extension(path: str) -> str:
    return os.path.splitext(path)[1].lower()

def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = 200):
    start = 0
    L = len(text)
    while start < L:
        end = start + chunk_size
        chunk = text[start:end]
        yield chunk
        start = end - overlap if end - overlap > start else end

def summarize_text(text: str, prompt_prefix: str = "Summarize the following content in 3 concise bullet points:") -> str:

    completion = client.chat.completions.create(
        model=summarization_model,
        messages=[
            {"role": "system", "content": "You are a concise summarizer."},
            {
                "role": "user",
                "content": f"{prompt_prefix}\n\n{text}",
            },
        ],
    )
    return completion.choices[0].message.content
