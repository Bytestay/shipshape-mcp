"""Reading local files for tools that accept a path instead of the content.

A path is only read when, after resolving symlinks, it sits inside the root (the environment variable
SHIPSHAPE_MCP_ROOT, or the current working directory when it is not set) and has an allowed extension.
"""
from __future__ import annotations

import os
from pathlib import Path

from mcp.server.mcpserver.exceptions import ToolError

ROOT_ENV = "SHIPSHAPE_MCP_ROOT"
ALLOWED_TEXT = "Dockerfile, Containerfile, *.dockerfile, *.yaml, *.yml, *.json"


def root() -> Path:
    return Path(os.environ.get(ROOT_ENV) or Path.cwd()).expanduser().resolve()


def _allowed(name: str) -> bool:
    n = name.lower()
    return (n.startswith(("dockerfile", "containerfile")) or n.endswith((".dockerfile", ".yaml", ".yml", ".json")))


def resolve(path: str) -> Path:
    base = root()
    given = Path(path).expanduser()
    p = (given if given.is_absolute() else base / given).resolve()
    if not p.is_relative_to(base):
        raise ToolError(f"{path} is outside the allowed folder {base} (set {ROOT_ENV} to allow another one).")
    if not p.is_file():
        raise ToolError(f"No such file: {path} (relative paths start from {base}).")
    if not _allowed(p.name):
        raise ToolError(f"{p.name} is not an allowed file type: {ALLOWED_TEXT}.")
    return p

def read_text(path: str, max_bytes: int) -> str:
    p = resolve(path)
    size = p.stat().st_size
    if size > max_bytes:
        raise ToolError(f"{p} is {size:,} bytes; the limit is {max_bytes:,}.")
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ToolError(f"{p} is not UTF-8 text.")
