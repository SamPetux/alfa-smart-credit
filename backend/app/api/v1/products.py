"""Каталог продуктов из БД (seed)."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import select

from backend.app.db.models import Product
from backend.app.identity.deps import DbSession, RequireAuth
from backend.app.schemas.common import ApiModel, MoneyStr
from backend.app.schemas.enums import ProductCode

router = APIRouter(tags=["products"])


class ProductOut(ApiModel):
    code: ProductCode
    title: str
    amount_min: MoneyStr
    amount_max: MoneyStr
    term_months: list[int]
    description: str | None = None


class ProductsResponse(ApiModel):
    products: list[ProductOut]


@router.get("/products", response_model=ProductsResponse)
def list_products(db: DbSession, _auth: RequireAuth) -> ProductsResponse:
    rows = db.scalars(select(Product).where(Product.active.is_(True)).order_by(Product.code)).all()
    products: list[ProductOut] = []
    for row in rows:
        limits = row.limits_json or {}
        products.append(
            ProductOut(
                code=ProductCode(row.code),
                title=str(limits.get("title") or row.code),
                amount_min=Decimal(str(limits.get("amount_min", "0.00"))),
                amount_max=Decimal(str(limits.get("amount_max", "0.00"))),
                term_months=list(limits.get("term_months") or []),
                description=limits.get("description"),
            )
        )
    return ProductsResponse(products=products)
