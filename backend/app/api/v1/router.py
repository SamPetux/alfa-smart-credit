"""Сборка API v1."""

from fastapi import APIRouter

from backend.app.api.v1 import applications, auth, demo, products

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(demo.router)
api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(applications.router)
