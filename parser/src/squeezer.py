#-*- coding: utf-8 -*-
from __future__ import annotations

from bs4 import BeautifulSoup, Tag
from src.utils.string import is_needle_at_end

import re as re


class Squeezer(object):
    @staticmethod
    def get_title(html_content: str) -> str | None:
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.title.string if soup.title else None

    @staticmethod
    def is_needle_at_end_tag_text(
        html_content: str,
        needle: str,
        ignore_case: bool = True
    ) -> bool:
        if ignore_case:
            html_content = html_content.lower()
            needle = needle.lower()

        for tag in BeautifulSoup(html_content, 'html.parser').find_all():
            if is_needle_at_end(tag.text.strip(), needle):
                return True

        return False

    @classmethod
    def squeeze(cls, html_content: str) -> dict[str, str] | None:
        key_data = {}

        soup = BeautifulSoup(html_content, 'html.parser')

        for tag in soup.find_all(('style', 'script')):
            tag.decompose()

        for tag in soup.find_all():
            if cls._get_valid_tag_count(tag) == 2:
                key_data.update(cls._extract_valid_key_value(tag))

        return key_data if key_data else None

    @classmethod
    def _get_valid_tag_count(cls, tag: Tag) -> int:
        count = 0

        if hasattr(tag, 'children'):
            for child_tag in tag.children:
                count += cls._get_valid_tag_count(child_tag)

        if not tag.name and tag.string and cls._process_text(tag.string):
            count += 1

        return count

    @classmethod
    def _extract_valid_key_value(cls, tag: Tag) -> dict[str, str] | None:
        kv_array = []

        def extract_text(tag: Tag) -> None:
            if len(kv_array) == 2:
                return

            if hasattr(tag, 'children'):
                for child_tag in tag.children:
                    extract_text(child_tag)

            if not tag.name and tag.string:
                processed_text = cls._process_text(tag.string)
                processed_text and kv_array.append(processed_text)

        extract_text(tag)

        return {kv_array[0]: kv_array[1]} if len(kv_array) == 2 else None

    @staticmethod
    def _process_text(text: str, bad_regexp_pattern: str = r'\.{2,}') -> str | None:
        cleaned_text = text.strip(':; ')
        if len(cleaned_text) == 1 or bool(re.search(bad_regexp_pattern, cleaned_text)): # or cleaned_text == ':'
            return None

        return cleaned_text
