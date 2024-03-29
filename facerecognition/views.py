import asyncio
from typing import Dict
from concurrent.futures import ProcessPoolExecutor

import aiohttp_jinja2
from aiohttp import web

from .worker import recognize, add_face
from .utils import Config


class SiteHandler:
    def __init__(self, conf: Config, executor: ProcessPoolExecutor) -> None:
        self._conf = conf
        self._executor = executor

    @aiohttp_jinja2.template('index.html')
    async def index(self, request: web.Request) -> Dict[str, str]:
        return {}

    async def recognize(self, request: web.Request) -> web.Response:
        form = await request.post()
        file_data = form['file'].file.read()
        form["file"].file.close()  # Not needed in aiohttp 4+.
        executor = request.app['executor']
        r = asyncio.get_event_loop().run_in_executor
        result_data = await r(executor, recognize, file_data)
        headers = {'Content-Type': 'application/json'}
        return web.Response(body=result_data, headers=headers)

    async def add_face(self, request: web.Request) -> web.Response:
        form = await request.post()
        name = form['name']
        file_data = form['file'].file.read()
        executor = request.app['executor']
        r = asyncio.get_event_loop().run_in_executor
        result_data = await r(executor, add_face, name, file_data)
        headers = {'Content-Type': 'application/json'}
        return web.Response(body=result_data, headers=headers)
