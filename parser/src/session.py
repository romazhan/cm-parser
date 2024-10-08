#-*- coding: utf-8 -*-
from __future__ import annotations

from curl_cffi.requests import AsyncSession


def create_async_client(headers: dict[str, str | int] | None = None) -> AsyncSession:
    return AsyncSession(headers=headers, impersonate='chrome110')
