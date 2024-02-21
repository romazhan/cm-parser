#-*- coding: utf-8 -*-
from __future__ import annotations

from typing import Iterable

from html import unescape
import re


def remove_cyrillic(string: str) -> str:
    return re.sub(r'[а-яё]', '', string, flags=re.IGNORECASE)

def remove_words(string: str, words: Iterable[str]) -> str:
    return ' '.join([word for word in string.split(' ') if word not in words])

def is_needle_at_end(haystack: str, needle: str) -> bool:
    index = haystack.find(needle)
    return index != -1 and not haystack[index + len(needle):]

def clear_string(string: str, strip_chars: str = ' ') -> str:
    return re.sub(r'\s+', ' ', unescape(
        re.sub('ё', 'е', string, flags=re.IGNORECASE)
    )).replace('”', '"').replace('“', '"').strip(strip_chars)
