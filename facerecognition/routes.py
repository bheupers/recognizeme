import pathlib

from aiohttp import web

from .views import SiteHandler
from .utils import Config

PROJECT_PATH = pathlib.Path(__file__).parent


def init_routes(app: web.Application, handler: SiteHandler) -> None:
    add_route = app.router.add_route

    add_route('GET', '/recognizeme/', handler.index, name='index')
    add_route('POST', '/recognizeme/recognize', handler.recognize, name='recognize')
    add_route('POST', '/recognizeme/add_face', handler.add_face, name='add_face')

    # added static dir
    app.router.add_static(
        "/recognizeme/static/", path=(PROJECT_PATH / 'static'), name='static'
    )
