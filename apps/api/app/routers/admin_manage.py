"""Authenticated admin CRUD (vocab, scenarios, users, dashboard)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, or_

from app.core.security import hash_password
from app.deps import ADMIN_ROLES, AdminUser, DbSession, SuperAdminUser
from app.models import RoleplaySession, Scenario, User, UserCard, Vocabulary
from app.schemas import (
    AdminDashboard,
    AdminScenarioCreate,
    AdminScenarioOut,
    AdminScenarioUpdate,
    AdminUserCreate,
    AdminUserUpdate,
    AdminVocabCreate,
    AdminVocabUpdate,
    PaginatedScenarios,
    PaginatedUsers,
    PaginatedVocab,
    UserOut,
    VocabOut,
)
from app.services.pinyin_util import ensure_pinyin, has_hanzi

router = APIRouter(prefix="/admin", tags=["admin-manage"])


@router.get("/dashboard", response_model=AdminDashboard)
def dashboard(_: AdminUser, db: DbSession) -> AdminDashboard:
    by_plan = {
        row[0] or "free": row[1]
        for row in db.query(User.plan, func.count(User.id)).group_by(User.plan).all()
    }
    by_role = {
        row[0] or "user": row[1]
        for row in db.query(User.role, func.count(User.id)).group_by(User.role).all()
    }
    by_hsk = {
        str(row[0]): row[1]
        for row in db.query(Vocabulary.hsk_level, func.count(Vocabulary.id))
        .group_by(Vocabulary.hsk_level)
        .order_by(Vocabulary.hsk_level)
        .all()
    }
    since = datetime.now(timezone.utc) - timedelta(days=7)
    users_new_7d = db.query(User).filter(User.created_at >= since).count()
    google_users = db.query(User).filter(User.google_sub.isnot(None)).count()
    paid_users = db.query(User).filter(User.plan.in_(("pro", "unlimit"))).count()

    return AdminDashboard(
        users=db.query(User).count(),
        vocab=db.query(Vocabulary).count(),
        scenarios=db.query(Scenario).count(),
        by_plan=by_plan,
        by_role=by_role,
        users_new_7d=users_new_7d,
        google_users=google_users,
        roleplay_sessions=db.query(RoleplaySession).count(),
        user_cards=db.query(UserCard).count(),
        by_hsk=by_hsk,
        paid_users=paid_users,
    )


# ---- Users ----


@router.get("/users", response_model=PaginatedUsers)
def list_users(
    _: AdminUser,
    db: DbSession,
    q: str | None = None,
    role: str | None = None,
    plan: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedUsers:
    query = db.query(User)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(User.email.ilike(like), User.display_name.ilike(like)))
    if role:
        query = query.filter(User.role == role)
    if plan:
        query = query.filter(User.plan == plan)
    total = query.count()
    items = (
        query.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedUsers(
        items=[UserOut.model_validate(u) for u in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/users", response_model=UserOut)
def create_user(body: AdminUserCreate, admin: AdminUser, db: DbSession) -> User:
    is_super = (admin.role or "") == "super_admin"
    if body.role == "admin" and not is_super:
        raise HTTPException(status_code=403, detail="Only Super Admin can create Admin")
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        display_name=body.display_name.strip(),
        role=body.role if is_super else "user",
        plan=body.plan if is_super else "free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: AdminUserUpdate,
    admin: AdminUser,
    db: DbSession,
) -> User:
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    target_role = target.role or "user"
    admin_role = admin.role or "user"
    is_super = admin_role == "super_admin"

    if not is_super and target_role in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Cannot edit Admin / Super Admin")

    if body.display_name is not None:
        target.display_name = body.display_name.strip()

    if body.password is not None:
        target.password_hash = hash_password(body.password)

    if body.role is not None or body.plan is not None:
        if not is_super:
            raise HTTPException(status_code=403, detail="Only Super Admin can change role/plan")
        if body.role is not None:
            if target.id == admin.id and body.role != "super_admin":
                other_supers = (
                    db.query(User)
                    .filter(User.role == "super_admin", User.id != admin.id)
                    .count()
                )
                if other_supers == 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot demote the only Super Admin",
                    )
            target.role = body.role
        if body.plan is not None:
            target.plan = body.plan

    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin: SuperAdminUser, db: DbSession) -> dict:
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    if (target.role or "") == "super_admin":
        other = db.query(User).filter(User.role == "super_admin", User.id != target.id).count()
        if other == 0:
            raise HTTPException(status_code=400, detail="Cannot delete the only Super Admin")
    db.delete(target)
    db.commit()
    return {"ok": True}


# ---- Vocab ----


@router.get("/vocab", response_model=PaginatedVocab)
def admin_list_vocab(
    _: AdminUser,
    db: DbSession,
    q: str | None = None,
    hsk_level: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedVocab:
    query = db.query(Vocabulary)
    if hsk_level is not None:
        query = query.filter(Vocabulary.hsk_level == hsk_level)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Vocabulary.hanzi.ilike(like),
                Vocabulary.pinyin.ilike(like),
                Vocabulary.meaning_vi.ilike(like),
                Vocabulary.meaning_en.ilike(like),
            )
        )
    total = query.count()
    items = (
        query.order_by(Vocabulary.hsk_level, Vocabulary.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedVocab(
        items=[VocabOut.model_validate(v) for v in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/vocab", response_model=VocabOut)
def create_vocab(body: AdminVocabCreate, _: AdminUser, db: DbSession) -> Vocabulary:
    data = body.model_dump()
    if has_hanzi(data.get("hanzi")):
        data["pinyin"] = ensure_pinyin(data.get("hanzi"), data.get("pinyin")) or data.get("pinyin")
    row = Vocabulary(**data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/vocab/{vocab_id}", response_model=VocabOut)
def update_vocab(
    vocab_id: int, body: AdminVocabUpdate, _: AdminUser, db: DbSession
) -> Vocabulary:
    row = db.get(Vocabulary, vocab_id)
    if not row:
        raise HTTPException(status_code=404, detail="Vocab not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    if has_hanzi(row.hanzi):
        row.pinyin = ensure_pinyin(row.hanzi, row.pinyin) or row.pinyin
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/vocab/{vocab_id}")
def delete_vocab(vocab_id: int, _: AdminUser, db: DbSession) -> dict:
    row = db.get(Vocabulary, vocab_id)
    if not row:
        raise HTTPException(status_code=404, detail="Vocab not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


# ---- Scenarios ----


@router.get("/scenarios", response_model=PaginatedScenarios)
def admin_list_scenarios(
    _: AdminUser,
    db: DbSession,
    q: str | None = None,
    track: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedScenarios:
    query = db.query(Scenario)
    if track:
        query = query.filter(Scenario.track == track)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(Scenario.title.ilike(like), Scenario.description.ilike(like))
        )
    total = query.count()
    items = (
        query.order_by(Scenario.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedScenarios(
        items=[AdminScenarioOut.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/scenarios", response_model=AdminScenarioOut)
def create_scenario(body: AdminScenarioCreate, _: AdminUser, db: DbSession) -> Scenario:
    row = Scenario(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/scenarios/{scenario_id}", response_model=AdminScenarioOut)
def update_scenario(
    scenario_id: int, body: AdminScenarioUpdate, _: AdminUser, db: DbSession
) -> Scenario:
    row = db.get(Scenario, scenario_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/scenarios/{scenario_id}")
def delete_scenario(scenario_id: int, _: AdminUser, db: DbSession) -> dict:
    row = db.get(Scenario, scenario_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
