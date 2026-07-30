from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel


class SpecField(BaseModel):
    name: str
    label: str
    value: Any
    display_value: str
    unit: str = ""


class SpecGroup(BaseModel):
    key: str
    label: str
    fields: list[SpecField]


class BoxItem(BaseModel):
    name: str
    quantity: str | None = None
    description: str | None = None


class ResourceLink(BaseModel):
    category: str
    label: str
    href: str
    badge: str | None = None


class Variant(BaseModel):
    sku: str
    name: str
    thumbnail_url: str | None = None


class Product(BaseModel):
    sku: str
    name: str
    short_description: str
    long_description: str
    technical_details: str
    spec_groups: list[SpecGroup]
    in_the_box: list[BoxItem]
    pinout_image_url: str | None = None
    resources: list[ResourceLink]
    variants: list[Variant]
    fetched_at: datetime

    def all_fields(self) -> list[SpecField]:
        return [f for group in self.spec_groups for f in group.fields]

    def field(self, name: str) -> SpecField | None:
        for f in self.all_fields():
            if f.name == name:
                return f
        return None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
