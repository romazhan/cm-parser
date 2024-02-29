#-*- coding: utf-8 -*-
from __future__ import annotations

from src.utils.sugar import nonstop
import json


class Green(object):
    _category_dump_file_path: str
    _category_dump: None | list[dict[any]]
    def __init__(self, category_dump_file_path: str) -> None:
        self._category_dump_file_path = category_dump_file_path
        self._category_dump = None

    @property
    def is_category_dump_loaded(self) -> bool:
        return bool(self._category_dump)

    @nonstop(5, timeout_sec=1.65)
    async def load_category_dump(self) -> list[dict[any]]:
        with open(self._category_dump_file_path, 'r', encoding='utf-8') as f:
            self._category_dump = json.load(f)

        return self._category_dump

    def get_attributes(self, category_id: int) -> list[dict[any]] | None:
        assert self._category_dump, 'category dump not loaded'

        for c in self._category_dump:
            if int(c['id']) == int(category_id):
                return c['attributes']

        return None
