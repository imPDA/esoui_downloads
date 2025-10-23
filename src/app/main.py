from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, Query, Request, Depends, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

from sqladmin import Admin

from app.services.addons import AddonsService, get_addons_service
from core.database import create_tables, ENGINE

from app.admin import DownloadsAdmin, AddonAdmin
from app.models import AddonDownloadSpeedResponse, AddonResponse, DownloadResponse, Filters, ReleaseResponse


BASE_FOLDER = Path(__file__).parent


app = FastAPI(title='ESOUI Charts')

app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)

app.mount('/static', StaticFiles(directory=BASE_FOLDER / 'static'), name='static')
templates = Jinja2Templates(directory=BASE_FOLDER / 'templates')


admin = Admin(app, ENGINE)

admin.add_view(AddonAdmin)
admin.add_view(DownloadsAdmin)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


@app.get('/')
async def search_page(
    request: Request,
    # addons: list[int] = Query(None)
):  
    # filters = Filters(addons=addons)

    # downloads = get_downloads(filters)

    # return templates.TemplateResponse(
    #     request=request,
    #     name='downloads.jinja',
    #     context={'downloads': downloads},
    # )
    
    return templates.TemplateResponse(
        request=request,
        name='search.jinja',
        # context={'downloads': downloads},
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
    addons_service: AddonsService = Depends(get_addons_service),
):
    filters = Filters(
        author=author,
        deprecated=deprecated,
    )

    downloads = addons_service.get_downloads(filters)
    for download in downloads:
        download['max'] = format_number(download['y'][-1])

    downloads.sort(key=lambda x: x['y'][-1], reverse=True)

    return templates.TemplateResponse(
        request=request,
        name='author.jinja',
        context={'downloads': downloads, 'addons_author': author}
    )


@app.get('/addon/{esoui_id:int}')
async def addon_page(
    request: Request,
    esoui_id: int,
    addons_service: AddonsService = Depends(get_addons_service),
):  
    filters = Filters(addons=[esoui_id])
    downloads = addons_service.get_downloads(filters)
    releases = addons_service.get_releases(esoui_id)
    download_speed = addons_service.get_download_speed(esoui_id)
    
    return templates.TemplateResponse(
        request=request,
        name='addon.jinja',
        context={
            'downloads': downloads, 
            'addon_name': downloads[0]['name'],
            'releases': releases,
            'download_speed': download_speed,
        }
    )


@app.get('/api/downloads', response_model=list[DownloadResponse])
async def api_downloads(
    addons: list[int] = Query(None),
    addons_service: AddonsService = Depends(get_addons_service),
):
    return addons_service.get_downloads(Filters(addons=addons))


@app.get('/api/author/{author:str}', response_model=list[DownloadResponse])
async def api_author_downloads(
    author: str,
    addons_service: AddonsService = Depends(get_addons_service),
):
    return addons_service.get_downloads(Filters(author=author))


@app.get('/api/addon/{esoui_id:int}', response_model=list[DownloadResponse])
async def api_addon_downloads(
    esoui_id: int,
    addons_service: AddonsService = Depends(get_addons_service),
):
    return addons_service.get_downloads(Filters(addons=[esoui_id]))


# @app.get('/api/addons', response_model=list[AddonResponse])
# async def api_addons():
#     return get_last_month_downloads()


@app.get('/api/addons', response_model=list[AddonResponse], response_model_exclude_unset=True)
async def api_addons(
    q: str = Query(None),
    addons_service: AddonsService = Depends(get_addons_service),
):
    if not q:
        return []
    
    return addons_service.search_for(q)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
