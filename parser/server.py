#-*- coding: utf-8 -*-
from __future__ import annotations

from configparser import ConfigParser

from fastapi import (
    FastAPI, APIRouter, Depends, Request, HTTPException
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from src.utils.sugar import datetime
from src.green import Green
from src.duck import Duck
from src.brain import (
    Brain, LinkSummary
)

import random, time, sys, os


_ROOT = os.path.dirname(sys.argv[0])
_ROOT and os.chdir(_ROOT)

_CONFIG_FILE_PATH = './config.ini'
_CATEGORY_DUMP_FILE_PATH = './category_dump.json'

class _APIface(object):
    class _AuthorizableRequest(BaseModel):
        secret: str

    class ParseRequest(_AuthorizableRequest):
        product_model: str
        category_id: int

    class ParseResponse(BaseModel):
        summary: list[LinkSummary]
        elapsed_time_sec: int
        parsers_used: int

def _register_routes(
    app_router: APIRouter,
    confdad: ConfigParser
) -> list[Depends]:
    green = Green(_CATEGORY_DUMP_FILE_PATH)
    duck = Duck(confdad.get('DUCK', 'region'))

    @app_router.post('/parse')
    async def _(request: _APIface.ParseRequest) -> _APIface.ParseResponse:
        request.product_model = request.product_model.strip()
        if not request.product_model:
            raise HTTPException(400, detail='empty product model')

        start_time = time.time()

        if not green.is_category_dump_loaded or random.randint(0, 12) == 0:
            await green.load_category_dump()

        attributes = green.get_attributes(request.category_id)
        if not attributes:
            raise HTTPException(424, detail=f'no attributes found ({request.category_id})')

        product_links = duck.get_links(
            request.product_model,
            timeout_sec=confdad.getfloat('DUCK', 'fetch_timeout_sec'),
            count_limit=confdad.getint('DUCK', 'link_count_limit')
        )
        if not product_links:
            raise HTTPException(424, detail='failed to get links to sites')

        summary = await Brain.get_product_summary(
            product_links,
            product_model=request.product_model,
            attributes=attributes,
            fetch_timeout_sec=confdad.getfloat('BRAIN', 'fetch_timeout_sec'),
            kv_len_range=confdad.gettupleint('BRAIN', 'kv_len_range'),
            k_threshold=confdad.getint('BRAIN', 'k_threshold')
        ) or []

        return _APIface.ParseResponse(
            summary=summary,
            elapsed_time_sec=int(time.time() - start_time),
            parsers_used=1
        )

    async def assert_secret(request: Request) -> None:
        if (await request.json()).get('secret') != confdad.get('API', 'secret'):
            raise HTTPException(401)

    return [Depends(assert_secret)]

_confdad = ConfigParser(converters={
    'tupleint': lambda l: tuple(
        int(v.strip()) for v in l.strip('()').split(',')
    )
})
assert _confdad.read(_CONFIG_FILE_PATH), f'{_CONFIG_FILE_PATH} not found'

_app = FastAPI(
    title='CM Parser API',
    description='CM Parser API',
    version='1.0.0',
    debug=_confdad.getboolean('SERVER', 'debug'),
    redoc_url='/'
)
_app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['POST']
)

_app_router = APIRouter()
_app.include_router(_app_router,
    dependencies=_register_routes(_app_router, _confdad)
)

if __name__ == '__main__':
    host = _confdad.get('SERVER', 'host')
    port = _confdad.getint('SERVER', 'port')

    try:
        if _confdad.getboolean('SERVER', 'reload'):
            uvicorn.run(
                '__main__:_app',
                host=host,
                port=port,
                reload=True,
                reload_includes=[
                    '*.ini', '*.json'
                ]
            )
        else:
            uvicorn.run(_app, host=host, port=port)
    except Exception as e:
        e_message = f'[{datetime()}][unhandled]: {str(e) or "@empty"}'

        with open('error.log', 'a', encoding='utf-8') as f:
            f.write(f'{e_message}\n')

        print(f'\n{e_message}')

        input('\n- Press Enter to exit...')
        sys.exit(1)
