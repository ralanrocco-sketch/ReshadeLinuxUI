"""Tiny parser for Steam's quoted KeyValues/VDF text files."""
import re
from pathlib import Path
from typing import Any
TOKEN = re.compile(r'\s*(?://[^\n]*|"(?:(?:\\.)|[^"\\])*"|\{|\})')
def _unquote(token: str) -> str:
    return re.sub(r'\\(["\\])', r'\1', token[1:-1])
def parse(text: str) -> dict[str, Any]:
    tokens=[]
    for match in TOKEN.finditer(text):
        token=match.group(0).strip()
        if token and not token.startswith("//"): tokens.append(token)
    pos=0
    def read_value():
        nonlocal pos
        if pos>=len(tokens): raise ValueError("Unexpected end of VDF data")
        token=tokens[pos]; pos+=1
        if token=="{":
            result={}
            while pos<len(tokens) and tokens[pos]!="}":
                if tokens[pos] in ("{","}"): raise ValueError("Expected a VDF key")
                key=_unquote(tokens[pos]); pos+=1; result[key]=read_value()
            if pos>=len(tokens): raise ValueError("Unclosed VDF block")
            pos+=1; return result
        if token=="}": raise ValueError("Unexpected closing VDF block")
        return _unquote(token)
    result={}
    while pos<len(tokens):
        if tokens[pos] in ("{","}"): raise ValueError("Expected a top-level VDF key")
        key=_unquote(tokens[pos]); pos+=1; result[key]=read_value()
    return result
def load(path: Path) -> dict[str, Any]:
    return parse(path.read_text(encoding="utf-8", errors="replace"))
