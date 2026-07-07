import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.center import DiagnosticCenter
from app.models.package import Package
from app.models.user import User, UserRole
from app.schemas.center import CenterCreate, CenterOut
from app.schemas.package import PackageCreate, PackageOut

router = APIRouter(prefix="/api/v1/centers", tags=["centers"])


@router.post("/me", response_model=CenterOut, status_code=status.HTTP_201_CREATED)
async def create_center_profile(
    payload: CenterCreate,
    current_user: User = Depends(require_role(UserRole.CENTER)),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(DiagnosticCenter).where(DiagnosticCenter.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Center profile already exists")

    center = DiagnosticCenter(user_id=current_user.id, **payload.model_dump())
    db.add(center)
    await db.commit()
    await db.refresh(center)
    return center


@router.get("/me", response_model=CenterOut)
async def get_my_center(
    current_user: User = Depends(require_role(UserRole.CENTER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DiagnosticCenter).where(DiagnosticCenter.user_id == current_user.id))
    center = result.scalar_one_or_none()
    if not center:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No center profile found")
    return center


@router.get("", response_model=list[CenterOut])
async def list_centers(city: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(DiagnosticCenter).where(DiagnosticCenter.is_approved.is_(True))
    if city:
        query = query.where(DiagnosticCenter.city.ilike(f"%{city}%"))
    result = await db.execute(query)
    return result.scalars().all()


async def _get_owned_center(current_user: User, db: AsyncSession) -> DiagnosticCenter:
    result = await db.execute(select(DiagnosticCenter).where(DiagnosticCenter.user_id == current_user.id))
    center = result.scalar_one_or_none()
    if not center:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Create a center profile first")
    return center


@router.post("/me/packages", response_model=PackageOut, status_code=status.HTTP_201_CREATED)
async def create_package(
    payload: PackageCreate,
    current_user: User = Depends(require_role(UserRole.CENTER)),
    db: AsyncSession = Depends(get_db),
):
    center = await _get_owned_center(current_user, db)
    package = Package(center_id=center.id, **payload.model_dump())
    db.add(package)
    await db.commit()
    await db.refresh(package)
    return package


@router.get("/{center_id}/packages", response_model=list[PackageOut])
async def list_center_packages(center_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Package).where(Package.center_id == center_id, Package.is_active.is_(True))
    )
    return result.scalars().all()
