import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import redis_client
from app.database import get_db
from app.dependencies import get_current_user
from app.models.center import DiagnosticCenter
from app.models.package import Package
from app.models.report import SymptomQuery
from app.models.user import User
from app.schemas.report import RecommendedPackage, SymptomCheckRequest, SymptomCheckResponse
from app.services import ai_service

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])
logger = logging.getLogger(__name__)


@router.post("/symptom-check", response_model=SymptomCheckResponse)
async def symptom_check(
    payload: SymptomCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Cache the active catalogue in Redis for 10 min - it rarely changes and this
    # endpoint can get hit repeatedly as a patient tweaks their symptom description.
    # Caching is an optimization, not a dependency: if Redis is unreachable we
    # fall straight back to Postgres rather than failing the whole request.
    cache_key = f"catalogue:{payload.city or 'all'}"
    try:
        cached = await redis_client.get(cache_key)
    except Exception:
        logger.warning("Redis unavailable, skipping cache read for %s", cache_key, exc_info=True)
        cached = None

    if cached is None:
        query = select(Package, DiagnosticCenter).join(
            DiagnosticCenter, Package.center_id == DiagnosticCenter.id
        ).where(Package.is_active.is_(True), DiagnosticCenter.is_approved.is_(True))
        if payload.city:
            query = query.where(DiagnosticCenter.city.ilike(f"%{payload.city}%"))
        rows = (await db.execute(query)).all()

        catalogue = [
            {
                "package_id": str(pkg.id),
                "name": pkg.name,
                "symptom_tags": pkg.symptom_tags or "",
                "test_type": pkg.test_type,
            }
            for pkg, _center in rows
        ]
        package_lookup = {str(pkg.id): (pkg, center) for pkg, center in rows}
    else:
        catalogue = json.loads(cached)
        # rebuild lookup fresh from DB by id (cheap) since we need live price/name
        ids = [c["package_id"] for c in catalogue]
        rows = (
            await db.execute(
                select(Package, DiagnosticCenter)
                .join(DiagnosticCenter, Package.center_id == DiagnosticCenter.id)
                .where(Package.id.in_(ids))
            )
        ).all()
        package_lookup = {str(pkg.id): (pkg, center) for pkg, center in rows}

    if cached is None:
        try:
            await redis_client.set(cache_key, json.dumps(catalogue), ex=600)
        except Exception:
            logger.warning("Redis unavailable, skipping cache write for %s", cache_key, exc_info=True)

    if not catalogue:
        return SymptomCheckResponse(recommended_packages=[], ai_reasoning="No active packages available to match against.")

    try:
        ai_result = ai_service.recommend_packages(payload.symptoms, catalogue)
    except RuntimeError as e:
        # e.g. GROQ_API_KEY not configured - a config problem, not a client error
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        logger.error("AI recommendation call failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI recommendation service is temporarily unavailable. Please try again shortly.",
        )
    recommended_ids = ai_result.get("recommended_package_ids", [])
    reasoning = ai_result.get("reasoning", "")

    recommended = []
    for pkg_id in recommended_ids:
        entry = package_lookup.get(pkg_id)
        if not entry:
            continue
        pkg, center = entry
        recommended.append(
            RecommendedPackage(
                package_id=pkg.id,
                name=pkg.name,
                center_name=center.center_name,
                test_type=pkg.test_type,
                price=float(pkg.price),
                match_reason=reasoning[:200],
            )
        )

    log = SymptomQuery(
        patient_id=current_user.id,
        symptoms_text=payload.symptoms,
        recommended_package_ids=recommended_ids,
        ai_reasoning=reasoning,
    )
    db.add(log)
    await db.commit()

    return SymptomCheckResponse(recommended_packages=recommended, ai_reasoning=reasoning)
