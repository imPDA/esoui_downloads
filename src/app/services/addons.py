from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from fastapi import Depends
from sqlalchemy import Row, func, literal_column, or_, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.schemas import AddonSchema, DownloadsSchema, UpdateSchema

from app.models import AddonDownloadSpeedResponse, DownloadResponse, Filters, ReleaseResponse


class AddonsService:
    def __init__(self, db: Session):
        self.db = db

    def _get_addons_downloads(self, filters: Filters) -> Sequence[Row]:
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

        # if not filters.addons and not filters.author:
        #     filters = Filters(
        #         addons=[4035, 4141, 4108, 4037, 4112, 4032, 4082]
        #     )

        if addons := filters.addons:
            get_addons = get_addons.where(DownloadsSchema.esoui_id.in_(addons))

        if author := filters.author:
            get_addons = get_addons.add_columns(AddonSchema.author).where(AddonSchema.author == author)

        if not filters.deprecated:
            get_addons = get_addons.where(AddonSchema.category != 157)

        return self.db.execute(get_addons).all()

    def get_downloads(self, filters: Filters) -> list[dict]:
        addons = self._get_addons_downloads(filters)  

        plotly_data = defaultdict(lambda: {'x': [], 'y': [], 'name': None})

        for addon in addons:  # TODO: fix very bad naming
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

    def get_last_month_downloads(self) -> Sequence[Row]:
        subq = (
            select(
                DownloadsSchema.esoui_id,
                func.min(DownloadsSchema.downloads).label('min'),
                func.max(DownloadsSchema.downloads).label('max'),
            )
            .where(
                DownloadsSchema.timestamp >= datetime.now(timezone.utc) - timedelta(days=30),
            )
            .group_by(
                DownloadsSchema.esoui_id,
            )
            .subquery()
        )

        downloads_per_last_30_days = (subq.c.max - subq.c.min).label('downloads_per_last_30_days')
        stmt = (
            select(
                AddonSchema.esoui_id,
                AddonSchema.title,
                AddonSchema.author,
                AddonSchema.category,
                downloads_per_last_30_days,
                # AddonSchema.favorites
            )
            .select_from(AddonSchema)
            .join(
                subq,
                AddonSchema.esoui_id == subq.c.esoui_id,
            )
            .order_by(downloads_per_last_30_days.desc().nulls_last())
        )

        return self.db.execute(stmt).all()

    def get_releases(self, addon_id: int) -> list[ReleaseResponse]:
        get_releases = (
            select(
                UpdateSchema.timestamp,
                UpdateSchema.version,
            )
            .where(UpdateSchema.esoui_id == addon_id)
            .order_by(UpdateSchema.timestamp.desc())
        )

        releases = self.db.execute(get_releases).all()

        responce = []
        for release in releases:
            responce.append(
                ReleaseResponse(
                    timestamp=release.timestamp,
                    version=release.version,
                ).model_dump(mode='json')
            )

        return responce

    def get_download_speed(self, addon_id: int) -> dict:
        ordered_downloads = (
            select(
                DownloadsSchema.timestamp,
                DownloadsSchema.downloads,
                func.lag(DownloadsSchema.timestamp, 1).over(order_by=DownloadsSchema.timestamp).label('prev_timestamp'),
                func.lag(DownloadsSchema.downloads, 1).over(order_by=DownloadsSchema.downloads).label('prev_downloads'),
            )
            .where(DownloadsSchema.esoui_id == addon_id)
            .cte('ordered_downloads')
        )

        speeds = (
            select(
                ordered_downloads.c.timestamp,
                # ordered_downloads.c.downloads,
                # literal_column('EXTRACT(EPOCH FROM (timestamp - prev_timestamp))').label('delta_time_seconds'),
                (ordered_downloads.c.downloads - ordered_downloads.c.prev_downloads).label('delta_downloads'),
                ((
                    (ordered_downloads.c.downloads - ordered_downloads.c.prev_downloads) / 
                    func.nullif(literal_column('EXTRACT(EPOCH FROM (timestamp - prev_timestamp))'), 0)
                ) * 3600).label('downloads_per_hour'),
            )
            .select_from(ordered_downloads)
            .offset(1)
            .subquery()
        )

        query = (
            select(
                speeds.c.timestamp,
                
                func.avg(speeds.c.downloads_per_hour)
                .over(
                    order_by=speeds.c.timestamp,
                    rows=(-2, 2),
                )
                .label('downloads_per_hour')
            )
        )

        results = self.db.execute(query).mappings().all()
        
        data = {'x': [], 'y': []}

        for result in results:
            if result.downloads_per_hour is None:  # TODO: make check in db
                continue

            data['x'].append(result.timestamp)
            data['y'].append(result.downloads_per_hour)

        return AddonDownloadSpeedResponse.model_validate(data).model_dump(mode='json')

    def search_for(self, q: str) -> Sequence[Row]:
        query = select(
            AddonSchema.esoui_id,
            AddonSchema.title,
            AddonSchema.author,
            AddonSchema.category,
        )

        try:
            esoui_id = int(q)
            query = query.where(AddonSchema.esoui_id == esoui_id)
        except ValueError:
            query = query.where(or_(
                AddonSchema.title.ilike(f'%{q}%'),
                AddonSchema.author.ilike(f'%{q}%'),
            ))

        return self.db.execute(query).all() 


def get_addons_service(db: Session = Depends(get_db)) -> AddonsService:
    return AddonsService(db)
