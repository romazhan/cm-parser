#-*- coding: utf-8 -*-
from __future__ import annotations

import time


def nonstop(
    limit: int | float = float('inf'),
    timeout_sec: int | float = 0
) -> None:
    def wrapper(func: callable) -> callable:
        def inner(*args: any, **kwargs: any) -> None:
            for attempt in range(limit):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    if attempt == limit - 1:
                        raise
                timeout_sec and time.sleep(timeout_sec)
        return inner
    return wrapper

def datetime(sec: bool = True) -> str:
    return time.strftime(f'%d.%m.%Y, %H:%M{":%S" if sec else ""}')
