from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.deps import CurrentUser, DbSession, award_xp, touch_streak
from app.models import UserCard, Vocabulary
from app.schemas import CardOut, ReviewRequest, VocabOut
from app.services.fsrs_service import ensure_cards_for_user, get_or_create_mission, review_card

router = APIRouter(tags=["vocab"])


@router.get("/vocab", response_model=list[VocabOut])
def list_vocab(
    db: DbSession,
    user: CurrentUser,
    hsk_level: int | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(Vocabulary)
    if hsk_level is not None:
        query = query.filter(Vocabulary.hsk_level == hsk_level)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Vocabulary.hanzi.ilike(like),
                Vocabulary.pinyin.ilike(like),
                Vocabulary.meaning_vi.ilike(like),
            )
        )
    rows = (
        query.order_by(Vocabulary.hsk_level, Vocabulary.frequency.nulls_last(), Vocabulary.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return rows


@router.get("/cards/due", response_model=list[CardOut])
def due_cards(db: DbSession, user: CurrentUser, limit: int = Query(20, ge=1, le=50)):
    ensure_cards_for_user(db, user.id, limit=30)
    now = datetime.now(timezone.utc)
    cards = (
        db.query(UserCard)
        .options(joinedload(UserCard.vocab))
        .filter(UserCard.user_id == user.id, UserCard.due <= now)
        .order_by(UserCard.due)
        .limit(limit)
        .all()
    )
    return cards


@router.post("/cards/{card_id}/review", response_model=CardOut)
def review(card_id: int, body: ReviewRequest, db: DbSession, user: CurrentUser):
    card = (
        db.query(UserCard)
        .options(joinedload(UserCard.vocab))
        .filter(UserCard.id == card_id, UserCard.user_id == user.id)
        .first()
    )
    if not card:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Card not found")
    reviewed = review_card(db, card, body.rating)
    touch_streak(user)
    award_xp(db, user, 5 if body.rating in ("good", "easy") else 2, "flashcard_review")
    mission = get_or_create_mission(db, user.id)
    _bump_mission(mission, "review" if reviewed.reps > 1 else "learn_words", db)
    db.commit()
    db.refresh(reviewed)
    return reviewed


def _bump_mission(mission, task_id: str, db: DbSession) -> None:
    tasks = list(mission.tasks or [])
    changed = False
    for task in tasks:
        if task.get("id") != task_id or task.get("done"):
            continue
        task["progress"] = int(task.get("progress", 0)) + 1
        if task["progress"] >= int(task.get("target", 1)):
            task["done"] = True
        changed = True
        break
    if changed:
        mission.tasks = tasks
        if all(t.get("done") for t in tasks) and not mission.completed:
            mission.completed = True
        db.add(mission)
