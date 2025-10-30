import os
import glob
import json
from typing import List, Dict, Any
from datetime import datetime
from pypdf import PdfReader
import docx
import pandas as pd
from tqdm import tqdm
import re

from src.utils import safe_path, get_extension, chunk_text, summarize_text
from config import SAFE_BASE_DIR, MAX_FILE_READ_BYTES, DEFAULT_CHUNK_SIZE


def list_files(directory: str, pattern: str = "*", recursive: bool = False) -> Dict[str, Any]:
    """
    List files in a directory. Returns list of paths (relative to SAFE_BASE_DIR).
    """
    dirpath = safe_path(directory)
    if not os.path.isdir(dirpath):
        return {"error": "NotADirectory", "message": f"{dirpath} is not a directory"}
    if recursive:
        pattern_path = os.path.join(dirpath, "**", pattern)
        files = glob.glob(pattern_path, recursive=True)
    else:
        pattern_path = os.path.join(dirpath, pattern)
        files = glob.glob(pattern_path)
    files = [os.path.abspath(f) for f in files if os.path.isfile(f)]

    rel = [os.path.relpath(f, SAFE_BASE_DIR) for f in files]
    return {"directory": os.path.relpath(dirpath, SAFE_BASE_DIR), "count": len(rel), "files": rel}


def list_directories(directory: str, recursive: bool = False) -> Dict[str, Any]:
    """
    List directories and subdirectories in a directory. Returns list of directory paths (relative to SAFE_BASE_DIR).
    """
    dirpath = safe_path(directory)
    if not os.path.isdir(dirpath):
        return {"error": "NotADirectory", "message": f"{dirpath} is not a directory"}
    
    directories = []
    
    if recursive:
        for root, dirs, files in os.walk(dirpath):
            for d in dirs:
                dir_path = os.path.join(root, d)
                directories.append(os.path.abspath(dir_path))
    else:
        for item in os.listdir(dirpath):
            item_path = os.path.join(dirpath, item)
            if os.path.isdir(item_path):
                directories.append(os.path.abspath(item_path))
    
    rel_dirs = [os.path.relpath(d, SAFE_BASE_DIR) for d in directories]
    rel_dirs.sort()
    
    return {
        "directory": os.path.relpath(dirpath, SAFE_BASE_DIR),
        "count": len(rel_dirs),
        "directories": rel_dirs
    }



def get_file_metadata(path: str) -> Dict[str, Any]:
    file_path = safe_path(os.path.join(SAFE_BASE_DIR, path) if not os.path.isabs(path) else path)
    if not os.path.exists(file_path):
        return {"error": "NotFound", "path": path}
    stat = os.stat(file_path)
    return {
        "path": os.path.relpath(file_path, SAFE_BASE_DIR),
        "size_bytes": stat.st_size,
        "modified": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
        "extension": get_extension(file_path)
    }


def read_file(path: str, max_chars: int = 20000) -> Dict[str, Any]:
    """
    Read and auto-parse file content. Returns text (possibly truncated) and metadata.
    Path should be relative to SAFE_BASE_DIR or absolute inside SAFE_BASE_DIR.
    """
    candidate = os.path.join(SAFE_BASE_DIR, path) if not os.path.isabs(path) else path
    file_path = safe_path(candidate)
    if not os.path.exists(file_path):
        return {"error": "NotFound", "path": path}
    if os.path.getsize(file_path) > MAX_FILE_READ_BYTES:
        return {"warning": "FileLarge", "message": "File exceeds max read size", "path": os.path.relpath(file_path, SAFE_BASE_DIR)}

    ext = get_extension(file_path)
    text = ""
    try:
        if ext in {".txt", ".md"}:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        elif ext == ".csv":
            df = pd.read_csv(file_path, nrows=200)
            text = df.to_csv(index=False)
        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            text = json.dumps(obj, indent=2, ensure_ascii=False)[: max_chars]
        elif ext == ".pdf":
            reader = PdfReader(file_path)
            pages = []
            for p in reader.pages:
                try:
                    pages.append(p.extract_text() or "")
                except Exception:
                    pages.append("")
            text = "\n\n".join(pages)
        elif ext == ".docx":
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs]
            text = "\n".join(paragraphs)
        else:
            with open(file_path, "rb") as f:
                data = f.read(10000) 
            text = f"<binary file, sampled {len(data)} bytes>"
    except Exception as e:
        return {"error": "ReadError", "message": str(e), "path": path}

    truncated = False
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n...[truncated]..."
        truncated = True

    return {
        "path": os.path.relpath(file_path, SAFE_BASE_DIR),
        "extension": ext,
        "size_bytes": os.path.getsize(file_path),
        "text": text,
        "truncated": truncated
    }


def read_files_iterative(paths: List[str], chunk_size: int = DEFAULT_CHUNK_SIZE) -> Dict[str, Any]:
    """
    Read multiple files, chunk large ones, summarize each chunk (via local summarizer or OpenAI),
    and return integrated summary + file-level outputs.
    """
    results = []
    integrated_summaries = []
    for p in tqdm(paths, desc="Reading files"):
        try:
            r = read_file(p, max_chars=10000000) 
            if r.get("error"):
                results.append({"path": p, "error": r})
                continue
            text = r.get("text", "")
            chunks = list(chunk_text(text, chunk_size=chunk_size))
            summaries = []
            for ch in chunks:
                try:
                    s = summarize_text(ch, prompt_prefix=f"Summarize the following chunk of {p}:")
                    summaries.append(s)
                except Exception as e:
                    summaries.append(f"[summarize_failed: {e}]")
            file_summary = "\n".join(summaries[:10])
            results.append({"path": p, "summary": file_summary, "chunks": len(chunks)})
            integrated_summaries.append(f"File: {p}\n{file_summary}")
        except Exception as e:
            results.append({"path": p, "error": str(e)})

    integrated = "\n\n".join(integrated_summaries)
 
    final_summary = integrated
    try:
        final_summary = summarize_text(integrated, prompt_prefix="Integrate and summarize the following file summaries into a concise overview:")
    except Exception:
        pass

    return {"files": results, "integrated_summary": final_summary}

def search_in_files(query: str, paths: List[str], use_regex: bool = False, max_results: int = 20) -> Dict[str, Any]:
    """
    Search query across list of files, returning list of matches with small contexts.
    """
    matches = []
    pattern = re.compile(query, re.IGNORECASE) if use_regex else None
    for p in paths:
        try:
            r = read_file(p, max_chars=5_000_000)
            if r.get("error"):
                continue
            text = r.get("text","")
            if use_regex:
                for m in pattern.finditer(text):
                    start = max(0, m.start()-120)
                    end = min(len(text), m.end()+120)
                    context = text[start:end]
                    matches.append({"path": p, "match": m.group(0), "context": context})
            else:
                idx = text.lower().find(query.lower())
                if idx != -1:
                    start = max(0, idx-120)
                    end = min(len(text), idx + len(query) + 120)
                    context = text[start:end]
                    matches.append({"path": p, "match": text[idx: idx+len(query)], "context": context})
            if len(matches) >= max_results:
                break
        except Exception:
            continue
    return {"query": query, "matches": matches[:max_results]}

tools_configuration = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory with optional pattern and recursion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Path to directory (relative or absolute)."},
                    "pattern": {"type": "string", "description": "Optional glob pattern, e.g. '*.pdf' or '*.csv'."},
                    "recursive": {"type": "boolean", "description": "If true, search subdirectories recursively."}
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directories",
            "description": "List directories and subdirectories in a directory. Returns only folder paths, not files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Path to directory (relative or absolute)."},
                    "recursive": {"type": "boolean", "description": "If true, list all subdirectories recursively."}
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_metadata",
            "description": "Return basic metadata for a file (size, mtime, mime/extension).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to inspect."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and return text content of a file. Auto-parses CSV/JSON/PDF/DOCX/txt. Will return a slice if file too large.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read."},
                    "max_chars": {"type": "integer", "description": "Max characters to return (for safety). Default is 4000."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_files_iterative",
            "description": "Read multiple files iteratively, chunk large files, summarize each chunk and return an integrated summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to read."
                    },
                    "chunk_size": {"type": "integer", "description": "Approx chars per chunk for chunking. Default is 4000."}
                },
                "required": ["paths"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_files",
            "description": "Search for a text or regex across one or more files and return matching contexts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query string or regex."},
                    "paths": {"type": "array", "items": {"type":"string"}, "description":"Files to search."},
                    "use_regex": {"type":"boolean", "description":"If true, treat query as regex."},
                    "max_results": {"type":"integer", "description":"Max matches to return."}
                },
                "required": ["query", "paths"]
            }
        }
    }
]
