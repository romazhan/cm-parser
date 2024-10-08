#-*- coding: utf-8 -*-
from __future__ import annotations

from pydantic import BaseModel
from curl_cffi.requests import AsyncSession

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
        'chocolate' # heheheha
    )

    @classmethod
    async def get_product_summary(
        cls,
        product_links: list[str],
        product_model: str,
        attributes: list[dict[any]],
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
                    attributes=attributes,
                    timeout_sec=fetch_timeout_sec,
                    kv_len_range=kv_len_range,
                    k_threshold=k_threshold
                ) for link in product_links
            ), return_exceptions=True)

        return list(filter(
            lambda ls: isinstance(ls, LinkSummary), links_summary
        )) or None

    @classmethod
    @nonstop(2, timeout_sec=1.7)
    async def _fetch_link_summary(
        cls,
        client: AsyncSession,
        link: str,
        product_model: str,
        attributes: list[dict[any]],
        timeout_sec: int | float,
        kv_len_range: tuple[int, int | float],
        k_threshold: int
    ) -> LinkSummary | None:
        matched_key_data = {}

        splitted_link = link.split('/')
        client.headers.update({
            'Referer': f'{splitted_link[0]}//{splitted_link[2]}/'
        })

        response = await client.get(link, timeout=timeout_sec)
        assert response.status_code == 200, 'status code not 200'

        response_title = Squeezer.get_title(response.text)
        if not response_title:
            return None

        lowered_product_model = product_model.lower()
        if lowered_product_model not in response_title.lower():
            return None

        # lowered_response_text = response.text.lower()
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

        key_data = Squeezer.squeeze(response.text)
        if not key_data:
            return None

        for k, v in key_data.items():
            if len(set((len(k), len(v))).intersection(
                range(kv_len_range[0], kv_len_range[1] + 1)
            )) != 2:
                continue

            for a in attributes:
                exed = fuzz_process.extractOne(
                    query=k,
                    choices=[a['name'], *a['synonyms']],
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=k_threshold
                ) if fuzz_utils.full_process(k) else None
                if not exed:
                    continue

                if not matched_key_data.get(a['name']) or matched_key_data[a['name']].score < exed[1]:
                    matched_key_data[a['name']] = _MatchedData(score=exed[1], value=clear_string(v))

        return LinkSummary(
            link=link,
            title=clear_string(response_title),
            key_data=matched_key_data
        ) if matched_key_data else None
