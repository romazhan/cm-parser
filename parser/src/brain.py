#-*- coding: utf-8 -*-
from pydantic import BaseModel
from aiohttp import ClientSession

from src.session import create_async_client
from src.squeezer import Squeezer
from src.utils.sugar import nonstop
from src.utils.string import (
    remove_cyrillic, remove_words, clear_string
)

from fuzzywuzzy import (
    utils as fuzz_utils, process as fuzz_process, fuzz
)

import asyncio


class _MatchedData(BaseModel):
    score: int
    value: str

class LinkSummary(BaseModel):
    link: str
    title: str
    key_data: dict[str, _MatchedData]

class Brain(object):
    _PRODUCT_MODEL_TEMPLATES = ('{},', '({})', '[{}]')
    _PRODUCT_LOWERED_COLORS = (
        'black', 'white', 'red', 'orange', 'yellow', 'green',
        'lightblue', 'blue', 'indigo', 'purple', 'violet', 'gray',
        'brown', 'pink', 'magenta', 'lime', 'coral', 'gold', 'silver',
        'chocolate' # hihihiha
    )

    @classmethod
    async def get_product_summary(
        cls,
        product_links: list[str],
        product_model: str,
        attribute_names: list[str],
        fetch_timeout_sec: int | float = 11.0,
        kv_len_range: tuple[int, int | float] = (1, float('inf')),
        k_threshold: int = 80
    ) -> list[LinkSummary] | None:
        async with create_async_client() as client:
            links_summary = await asyncio.gather(*(
                cls._fetch_link_summary(
                    client,
                    link=link,
                    product_model=product_model,
                    attribute_names=attribute_names,
                    timeout_sec=fetch_timeout_sec,
                    kv_len_range=kv_len_range,
                    k_threshold=k_threshold
                ) for link in product_links
            ), return_exceptions=True)

        return list(filter(
            lambda ls: isinstance(ls, LinkSummary), links_summary
        )) or None

    @classmethod
    @nonstop(3, timeout_sec=1.7)
    async def _fetch_link_summary(
        cls,
        client: ClientSession,
        link: str,
        product_model: str,
        attribute_names: list[str],
        timeout_sec: int | float,
        kv_len_range: tuple[int, int | float],
        k_threshold: int
    ) -> LinkSummary | None:
        matched_key_data = {}

        async with client.get(link, timeout=timeout_sec) as response:
            assert response.status == 200, 'status code not 200'

            response_text = await response.text()

            response_title = Squeezer.get_title(response_text)
            if not response_title:
                return None

            lowered_product_model = product_model.lower()
            if lowered_product_model not in response_title.lower():
                return None

            # lowered_response_text = response_text.lower()
            # if not any(pmt.format(lowered_product_model) in lowered_response_text
            #     for pmt in cls._PRODUCT_MODEL_TEMPLATES
            # ) and not Squeezer.is_needle_at_end_tag_text(
            #     remove_words(
            #         remove_cyrillic(lowered_response_text),
            #         cls._PRODUCT_LOWERED_COLORS
            #     ),
            #     lowered_product_model,
            #     ignore_case=False
            # ):
            #     return None

            key_data = Squeezer.squeeze(response_text)
            if not key_data:
                return None

            for k, v in key_data.items():
                if len(set((len(k), len(v))).intersection(
                    range(kv_len_range[0], kv_len_range[1] + 1
                ))) != 2:
                    continue

                exed = fuzz_process.extractOne(
                    query=k,
                    choices=attribute_names,
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=k_threshold
                ) if fuzz_utils.full_process(k) else None
                if not exed:
                    continue

                if not matched_key_data.get(exed[0]) or matched_key_data[exed[0]].score < exed[1]:
                    matched_key_data[exed[0]] = _MatchedData(score=exed[1], value=v)

        return LinkSummary(
            link=link,
            title=clear_string(response_title),
            key_data={
                k: _MatchedData(
                    score=matched_data.score,
                    value=clear_string(matched_data.value)
                ) for k, matched_data in matched_key_data.items()
            }
        ) if matched_key_data else None
