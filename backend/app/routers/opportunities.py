from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..mappers import opportunity_to_out
from ..models import Opportunity
from ..schemas import OpportunityList, OpportunityOut
from ..search_text import query_keys
from ..services.discovery import visible_opportunities_stmt

router = APIRouter()

SECTORS = ("trade", "industry", "agriculture", "tourism")


@router.get("/opportunities", response_model=OpportunityList)
def list_opportunities(
    sector: Optional[str] = Query(None, description=" | ".join(SECTORS)),
    q: Optional[str] = Query(None, max_length=100),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = visible_opportunities_stmt()
    if sector:
        stmt = stmt.where(Opportunity.sector == sector)
    keys = query_keys(q)
    if keys:
        n, c = keys
        stmt = stmt.where(
            or_(Opportunity.search_text.contains(n, autoescape=True), Opportunity.search_compact.contains(c, autoescape=True))
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Opportunity.sector, Opportunity.title_fa, Opportunity.id).limit(limit).offset(offset)).all()
    return OpportunityList(items=[opportunity_to_out(o) for o in rows], total=total)


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityOut)
def get_opportunity(opportunity_id: str, db: Session = Depends(get_db)):
    row = db.scalar(visible_opportunities_stmt().where(Opportunity.id == opportunity_id))
    if row is None:
        raise HTTPException(404, "Opportunity not found")
    return opportunity_to_out(row)
