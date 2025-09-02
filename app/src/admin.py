from sqladmin import ModelView
from sqladmin.filters import AllUniqueStringValuesFilter

from common.infra.database.schemas import AddonSchema, DownloadsSchema


class DownloadsAdmin(ModelView, model=DownloadsSchema):
    column_list = [DownloadsSchema.esoui_id, DownloadsSchema.downloads, DownloadsSchema.timestamp]
    name = 'Download'
    icon = 'fa-solid fa-cloud-arrow-down'

    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = False


class AddonAdmin(ModelView, model=AddonSchema):
    column_list = [AddonSchema.esoui_id, AddonSchema.title, AddonSchema.author, AddonSchema.category, AddonSchema.url]
    column_filters = [
        AllUniqueStringValuesFilter(AddonSchema.category),
    ]

    name = 'Addon'
    icon = 'fa-solid fa-puzzle-piece'
    column_searchable_list = [AddonSchema.title, AddonSchema.author]
    column_sortable_list = [AddonSchema.esoui_id, AddonSchema.title, AddonSchema.author]
    column_default_sort = [(AddonSchema.esoui_id, False)]

    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = False
