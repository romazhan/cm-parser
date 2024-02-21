#-*- coding: utf-8 -*-
from __future__ import annotations

from configparser import ConfigParser

from src.utils.sugar import nonstop
from src.green import Green
from src.duck import Duck
from src.brain import Brain

import asyncio, sys, os


_CONFIG_FILE_PATH = './config.ini'
_CATEGORY_DUMP_FILE_PATH = './category_dump.json'

@nonstop(2)
def _get_product_model() -> str:
    product_model = input('[*] input product model: ').strip()
    assert product_model, 'no product model'

    return product_model

@nonstop(2)
def _get_category_id() -> int:
    category_id = int(input('[*] input category id: '))
    assert category_id, 'no category id'

    return category_id

async def _main() -> None:
    confdad = ConfigParser(converters={
        'tupleint': lambda l: tuple(
            int(v.strip()) for v in l.strip('()').split(',')
        )
    })
    assert confdad.read(_CONFIG_FILE_PATH), f'{_CONFIG_FILE_PATH} not found'

    product_model = _get_product_model()
    product_category_id = _get_category_id()

    green = Green(_CATEGORY_DUMP_FILE_PATH)
    await green.load_category_dump()

    attribute_names = green.get_attribute_fields('name', product_category_id)
    assert attribute_names, 'no attributes found'

    duck = Duck(confdad.get('DUCK', 'region'))
    product_links = duck.get_links(
        product_model,
        timeout_sec=confdad.getfloat('DUCK', 'fetch_timeout_sec'),
        count_limit=confdad.getint('DUCK', 'link_count_limit'),
    )
    assert product_links, 'no product links'

    summary = await Brain.get_product_summary(
        product_links,
        product_model=product_model,
        attribute_names=attribute_names,
        fetch_timeout_sec=confdad.getfloat('BRAIN', 'fetch_timeout_sec'),
        kv_len_range=confdad.gettupleint('BRAIN', 'kv_len_range'),
        k_threshold=confdad.getint('BRAIN', 'k_threshold')
    )
    print(f'\n[result]: {summary}')

if __name__ == '__main__':
    ROOT = os.path.dirname(sys.argv[0])
    ROOT and os.chdir(ROOT)

    asyncio.run(_main())
