#-*- coding: utf-8 -*-
from __future__ import annotations

from duckduckgo_search import DDGS
from src.utils.sugar import nonstop


class Duck(object):
    _BAD_LINK_SUBS = () # ('://www.site',)
    _QUERY_PREFIXES = {
        'ru-ru': 'Характеристики товара',
        'us-en': 'Product specifications'
    }

    _region: str
    def __init__(self, region: str) -> None:
        self._region = region

    def get_links(self, product_model: str, timeout_sec: float | int, count_limit: int) -> list[str] | None:
        try:
            links = self._fetch_links(
                product_model,
                timeout_sec=timeout_sec,
                count_limit=count_limit
            )
        except:
            links = None

        return links

    @nonstop(4, timeout_sec=4.15)
    def _fetch_links(self, product_model: str, timeout_sec: float | int, count_limit: int) -> list[str]:
        links = [
            r['href'] for r in DDGS(timeout=timeout_sec).text(
                f'{self._get_query_prefix(self._region)}: {product_model}',
                region=self._region,
                max_results=count_limit
            ) if not any(s in r['href'] for s in self._BAD_LINK_SUBS)
        ]
        assert links, 'no links'

        return list(set(links))

    @classmethod
    def _get_query_prefix(cls, region: str) -> str | None:
        return cls._QUERY_PREFIXES.get(region, cls._QUERY_PREFIXES['ru-ru'])
