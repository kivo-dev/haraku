"""initial schema: categories, places, place_images, opportunities

Hand-written to match app/models.py exactly (tests/test_migrations.py compares the two).

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("key", sa.String(40), primary_key=True),
        sa.Column("title_fa", sa.String(100), nullable=False),
        sa.Column("title_en", sa.String(100), nullable=False),
        sa.Column("sort", sa.Integer(), nullable=False),
    )

    op.create_table(
        "places",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("category_key", sa.String(40), sa.ForeignKey("categories.key"), nullable=False),
        sa.Column("name_fa", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=False),
        sa.Column("area_fa", sa.String(200), nullable=False),
        sa.Column("area_en", sa.String(200), nullable=False),
        sa.Column("summary_fa", sa.Text(), nullable=False),
        sa.Column("summary_en", sa.Text(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("featured", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("verification", sa.String(20), nullable=False),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("search_compact", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_places_status", "places", ["status"])
    op.create_index("ix_places_status_category", "places", ["status", "category_key"])
    op.create_index("ix_places_lat_lng", "places", ["lat", "lng"])

    op.create_table(
        "place_images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("place_id", sa.String(80), sa.ForeignKey("places.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("caption_fa", sa.String(300), nullable=False),
        sa.Column("caption_en", sa.String(300), nullable=False),
        sa.Column("sort", sa.Integer(), nullable=False),
    )
    op.create_index("ix_place_images_place_id", "place_images", ["place_id"])

    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("sector", sa.String(40), nullable=False),
        sa.Column("title_fa", sa.String(200), nullable=False),
        sa.Column("title_en", sa.String(200), nullable=False),
        sa.Column("summary_fa", sa.Text(), nullable=False),
        sa.Column("summary_en", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("verification", sa.String(20), nullable=False),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("search_compact", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_opportunities_sector", "opportunities", ["sector"])
    op.create_index("ix_opportunities_status", "opportunities", ["status"])


def downgrade() -> None:
    op.drop_index("ix_opportunities_status", table_name="opportunities")
    op.drop_index("ix_opportunities_sector", table_name="opportunities")
    op.drop_table("opportunities")
    op.drop_index("ix_place_images_place_id", table_name="place_images")
    op.drop_table("place_images")
    op.drop_index("ix_places_lat_lng", table_name="places")
    op.drop_index("ix_places_status_category", table_name="places")
    op.drop_index("ix_places_status", table_name="places")
    op.drop_table("places")
    op.drop_table("categories")
