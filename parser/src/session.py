#-*- coding: utf-8 -*-
from aiohttp import ClientSession


def create_async_client(headers: dict[str, str | int] | None = None) -> ClientSession:
    _headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/119.0.0.0 Safari/537.36'
        )
    }
    headers and _headers.update(headers)

    return ClientSession(headers=_headers)
