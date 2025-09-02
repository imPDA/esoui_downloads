from collections import defaultdict
from datetime import datetime
import logging
from pathlib import Path
from typing import Iterable, Optional

from fastapi import FastAPI, Query, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

from pydantic import BaseModel
from sqlalchemy import select

from sqladmin import Admin

from common.infra.database.addons import create_tables, get_db, engine
from common.infra.database.schemas import DownloadsSchema, AddonSchema, UpdateSchema

from .admin import DownloadsAdmin, AddonAdmin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


SOURCE_FOLDER = Path(__file__).parent


app = FastAPI(title='ESOUI Charts')
admin = Admin(app, engine)

admin.add_view(AddonAdmin)
admin.add_view(DownloadsAdmin)

app.mount('/static', StaticFiles(directory=SOURCE_FOLDER / 'static'), name='static')
templates = Jinja2Templates(directory=SOURCE_FOLDER / 'templates')


create_tables()


class DownloadResponse(BaseModel):
    name: str
    x: list[datetime]
    y: list[int]
    author: Optional[str] = None
    max: Optional[int] = None


class ReleaseResponse(BaseModel):
    timestamp: datetime
    version: str


class Filters(BaseModel):
    addons: Optional[list[int]] = None
    author: Optional[str] = None
    deprecated: Optional[bool] = False


def get_downloads(filters: Filters) -> list[dict]:
    get_addons = (
        select(
            DownloadsSchema.esoui_id,
            DownloadsSchema.timestamp,
            DownloadsSchema.downloads,
            AddonSchema.title,
        )
        .join(AddonSchema)
        .order_by(DownloadsSchema.timestamp)
    )

    if not filters.addons and not filters.author:
        filters = Filters(
            addons=[4035, 4141, 4108, 4037, 4112, 4032, 4082]
        )

    if addons := filters.addons:
        get_addons = get_addons.where(DownloadsSchema.esoui_id.in_(addons))
    
    if author := filters.author:
        get_addons = get_addons.add_columns(AddonSchema.author).where(AddonSchema.author == author)

    if not filters.deprecated:
        get_addons = get_addons.where(AddonSchema.category != 157)

    with get_db() as db:
        addons = db.execute(get_addons).all()

    plotly_data = defaultdict(lambda: {'x': [], 'y': [], 'name': None})

    for addon in addons:
        addon_id = addon.esoui_id
        plotly_data[addon_id]['name'] = f'{addon.title:.20} ({addon_id})'
        plotly_data[addon_id]['x'].append(addon.timestamp)
        plotly_data[addon_id]['y'].append(addon.downloads)
        
        # if author:
        #     plotly_data[addon_id]['author'] = result.author

    responce = []
    for data in plotly_data.values():
        responce.append(DownloadResponse(**data).model_dump(mode='json'))

    return responce


def get_releases(addon_id: int) -> list[ReleaseResponse]:
    get_releases = (
        select(
            UpdateSchema.timestamp,
            UpdateSchema.version,
        )
        .where(UpdateSchema.esoui_id == addon_id)
        .order_by(UpdateSchema.timestamp.desc())
    )

    with get_db() as db:
        releases = db.execute(get_releases).all()

    responce = []
    for release in releases:
        responce.append(
            ReleaseResponse(
                timestamp=release.timestamp,
                version=release.version,
            ).model_dump(mode='json')
        )

    return responce


@app.get('/')
async def downloads_page(
    request: Request,
    addons: list[int] = Query(None)
):  
    filters = Filters(addons=addons)

    downloads = get_downloads(filters)

    return templates.TemplateResponse(
        request=request,
        name='esoui-downloads.html',
        context={'downloads': downloads},
    )


def format_number(num):
    if num >= 1_000_000_000:
        return f'{num / 1_000_000_000:.2f}B'
    elif num >= 1_000_000:
        return f'{num / 1_000_000:.2f}M'
    elif num >= 1_000:
        return f'{num / 1_000:.2f}K'
    else:
        return str(num)


@app.get('/author/{author:str}')
async def author(
    request: Request,
    author: str,
    deprecated: bool = Query(None),
):
    filters = Filters(
        author=author,
        deprecated=deprecated,
    )

    downloads = get_downloads(filters)
    for download in downloads:
        download['max'] = format_number(download['y'][-1])

    downloads.sort(key=lambda x: x['y'][-1], reverse=True)

    return templates.TemplateResponse(
        request=request,
        name='esoui-downloads-author.html',
        context={'downloads': downloads, 'addons_author': author}
    )


@app.get('/addon/{esoui_id:int}')
async def addon_page(
    request: Request,
    esoui_id: int,
):  
    filters = Filters(addons=[esoui_id])
    downloads = get_downloads(filters)
    releases = get_releases(esoui_id)
    
    return templates.TemplateResponse(
        request=request,
        name='esoui-downloads-single.html',
        context={
            'downloads': downloads, 
            'addon_name': downloads[0]['name'],
            'releases': releases,
        }
    )


@app.get('/api/downloads', response_model=list[DownloadResponse])
async def api_downloads(addons: list[int] = Query(None)):
    return get_downloads(Filters(addons=addons))


@app.get('/api/author/{author:str}', response_model=list[DownloadResponse])
async def api_author_downloads(author: str):
    return get_downloads(Filters(author=author))


@app.get('/api/addon/{esoui_id:int}', response_model=list[DownloadResponse])
async def api_addon_downloads(esoui_id: int):
    return get_downloads(Filters(addons=[esoui_id,]))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
