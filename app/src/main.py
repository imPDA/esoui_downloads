from collections import defaultdict
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Query, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

from pydantic import BaseModel
from sqlalchemy import select

from common.infra.database.addons import create_tables, get_db
from common.infra.database.schemas import DownloadsSchema, AddonSchema


SOURCE_FOLDER = Path(__file__).parent


app = FastAPI(title='ESOUI Downloads')

app.mount('/static', StaticFiles(directory=SOURCE_FOLDER / 'static'), name='static')
templates = Jinja2Templates(directory=SOURCE_FOLDER / 'templates')


create_tables()


class DownloadResponse(BaseModel):
    name: str
    x: list[datetime]
    y: list[int]


@app.get('/')
async def downloads_chart(request: Request):
    return templates.TemplateResponse(
        request=request, name='esoui-downloads.html'
    )


@app.get('/api/downloads', response_model=list[DownloadResponse])
async def api_downloads(addons: list[int] = Query(None)):
    get_data = (
        select(
            DownloadsSchema.esoui_id,
            DownloadsSchema.timestamp,
            DownloadsSchema.downloads,
            AddonSchema.title,
        )
        .join(AddonSchema)
        .order_by(DownloadsSchema.timestamp)
    )

    if not addons:
        addons = [4035, 4141, 4108, 4037, 4112, 4032, 4082]
    
    get_data = get_data.where(DownloadsSchema.esoui_id.in_(addons))

    with get_db() as db:
        results = db.execute(get_data).all()

    plotly_data = defaultdict(lambda: {'x': [], 'y': [], 'name': None})
    
    for result in results:
        addon_id = result.esoui_id
        plotly_data[addon_id]['name'] = result.title
        plotly_data[addon_id]['x'].append(result.timestamp)
        plotly_data[addon_id]['y'].append(result.downloads)

    return plotly_data.values()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
