import argparse
import asyncio
import os
import pathlib

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict

import trafaret as t
from aiohttp import web
from trafaret_config import commandline
from .worker import warm, clean


PATH = pathlib.Path(__file__).parent.parent
settings_file = os.environ.get('SETTINGS_FILE', 'api.dev.yml')
DEFAULT_CONFIG_PATH = PATH / 'config' / settings_file


CONFIG_TRAFARET = t.Dict({
    t.Key('app'): t.Dict({
        t.Key('host'): t.String(),
        t.Key('port'): t.Int[0: 2 ** 16],
        t.Key('detection_method'): t.String,
    }),
    t.Key('workers'): t.Dict({
        t.Key('max_workers'): t.Int[1:1024],
        t.Key('encodings_path'): t.String,
    }),
})


@dataclass(frozen=True)
class AppConfig:
    host: str
    port: int


@dataclass(frozen=True)
class WorkersConfig:
    max_workers: int
    encodings_path: str
    detection_method: str


@dataclass(frozen=True)
class Config:
    app: AppConfig
    workers: WorkersConfig


def config_from_dict(d: Dict[str, Any]) -> Config:
    app_config = AppConfig(  # type: ignore
        host=d['app']['host'],
        port=d['app']['port'])
    workers_config = WorkersConfig(  # type: ignore
        max_workers=d['workers']['max_workers'],
        encodings_path=d['workers']['encodings_path'],
        detection_method=d['app']['detection_method']
    )
    return Config(app=app_config, workers=workers_config)  # type: ignore


def get_config(argv: Any = None) -> Config:
    ap = argparse.ArgumentParser()
    commandline.standard_argparse_options(
        ap, default_config=DEFAULT_CONFIG_PATH
    )
    options = ap.parse_args(argv)
    d = commandline.config_from_options(options, CONFIG_TRAFARET)
    return config_from_dict(d)


def init_config(app: web.Application, config: Config) -> None:
    app['config'] = config


async def init_workers(
    app: web.Application, conf: WorkersConfig
) -> ProcessPoolExecutor:
    n = conf.max_workers
    executor = ProcessPoolExecutor(max_workers=n)
    path = str(PATH / conf.encodings_path)
    detection_method = conf.detection_method
    loop = asyncio.get_event_loop()
    run = loop.run_in_executor
    fs = [run(executor, warm, path, detection_method) for i in range(0, n)]
    await asyncio.gather(*fs)

    async def close_executor(app: web.Application) -> None:
        loop1 = asyncio.get_event_loop()
        run1 = loop1.run_in_executor
        fs1 = [run1(executor, clean) for i in range(0, n)]
        await asyncio.shield(asyncio.gather(*fs1))
        executor.shutdown(wait=True)

    app.on_cleanup.append(close_executor)
    app['executor'] = executor
    return executor
