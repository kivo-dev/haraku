from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .constants import PUBLISHED, VERIFIED  # noqa: F401  (re-exported)
from .search_text import build_search_fields


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Category(Base):
    """Place categories. New ones are added as rows, no code change in the backend.
    (The frontend supports HARAKO approved top-level categories; keys are shared API contract.)"""

    __tablename__ = "categories"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    title_fa: Mapped[str] = mapped_column(String(100))
    title_en: Mapped[str] = mapped_column(String(100))
    sort: Mapped[int] = mapped_column(Integer, default=0)

    def __str__(self) -> str:  # shown in the admin panel dropdowns
        return f"{self.title_fa} ({self.key})"


class Place(Base):
    """HARAKO's OWN place record: the source of truth. Data from Neshan/OSM is never copied in
    automatically (licences not checked yet); `source` says where each record came from."""

    __tablename__ = "places"
    __table_args__ = (
        Index("ix_places_status_category", "status", "category_key"),
        Index("ix_places_lat_lng", "lat", "lng"),  # bounding-box pre-filter of nearby queries
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)  # slug, also the image file name
    category_key: Mapped[str] = mapped_column(ForeignKey("categories.key"))
    name_fa: Mapped[str] = mapped_column(String(200))
    name_en: Mapped[str] = mapped_column(String(200), default="")
    area_fa: Mapped[str] = mapped_column(String(200), default="")
    area_en: Mapped[str] = mapped_column(String(200), default="")
    summary_fa: Mapped[str] = mapped_column(Text, default="")
    summary_en: Mapped[str] = mapped_column(Text, default="")

    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    verification: Mapped[str] = mapped_column(String(20), default="unverified")
    source: Mapped[str] = mapped_column(String(40), default="manual")  # manual | seed-sample | osm | ...
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    search_text: Mapped[str] = mapped_column(Text, default="")
    search_compact: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    category: Mapped["Category"] = relationship()
    images: Mapped[list["PlaceImage"]] = relationship(
        back_populates="place", order_by="PlaceImage.sort", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return f"{self.name_fa} ({self.id})"


class PlaceImage(Base):
    __tablename__ = "place_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    place_id: Mapped[str] = mapped_column(ForeignKey("places.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    caption_fa: Mapped[str] = mapped_column(String(300), default="")
    caption_en: Mapped[str] = mapped_column(String(300), default="")
    sort: Mapped[int] = mapped_column(Integer, default=0)

    place: Mapped[Place] = relationship(back_populates="images")


class Opportunity(Base):
    """Economic opportunity. A different kind of content from a tourist place, with its own life cycle."""

    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    sector: Mapped[str] = mapped_column(String(40), index=True)  # trade | industry | agriculture | tourism
    title_fa: Mapped[str] = mapped_column(String(200))
    title_en: Mapped[str] = mapped_column(String(200), default="")
    summary_fa: Mapped[str] = mapped_column(Text, default="")
    summary_en: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    verification: Mapped[str] = mapped_column(String(20), default="unverified")
    source: Mapped[str] = mapped_column(String(40), default="manual")
    search_text: Mapped[str] = mapped_column(Text, default="")
    search_compact: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


# The search columns are filled automatically on every insert/update, whoever writes the row
# (admin panel, seed script, a future API), so nobody has to remember to compute them.
def _fill_place_search(mapper, connection, target: Place) -> None:  # noqa: ARG001
    target.search_text, target.search_compact = build_search_fields(
        target.name_fa, target.name_en, target.area_fa, target.area_en, target.summary_fa, target.summary_en
    )


def _fill_opportunity_search(mapper, connection, target: Opportunity) -> None:  # noqa: ARG001
    target.search_text, target.search_compact = build_search_fields(
        target.title_fa, target.title_en, target.summary_fa, target.summary_en
    )


for _evt in ("before_insert", "before_update"):
    event.listen(Place, _evt, _fill_place_search)
    event.listen(Opportunity, _evt, _fill_opportunity_search)
