from fastapi import APIRouter

from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.members import router as members_router
from app.api.roles import router as roles_router
from app.api.tenants import router as tenants_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, tags=["auth"])
router.include_router(tenants_router, tags=["tenants"])
router.include_router(members_router, tags=["members"])
router.include_router(roles_router, tags=["roles"])
router.include_router(audit_router, tags=["audit"])
