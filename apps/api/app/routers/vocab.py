from datetime import datetime, timedelta, timezone
import random

from fastapi import APIRouter, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import contains_eager, joinedload

from app.deps import CurrentUser, DbSession, award_xp, touch_streak
from app.models import UserCard, Vocabulary
from app.schemas import (
    CardOut,
    DeckHskOut,
    DecksOut,
    DeckTopicOut,
    LearnedCardOut,
    ReviewRequest,
    VocabOut,
    VocabTopicOut,
)
from app.services.fsrs_service import ensure_cards_for_user, get_or_create_mission, review_card

router = APIRouter(tags=["vocab"])


def _daily_review_cutoff(now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    return now - timedelta(days=1)


def daily_review_stats(db: DbSession, user_id: int) -> tuple[int, bool]:
    """Eligible = learned (reps>=1) and last reviewed at least 1 day ago."""
    cutoff = _daily_review_cutoff()
    count = (
        db.query(UserCard)
        .filter(
            UserCard.user_id == user_id,
            UserCard.reps >= 1,
            UserCard.last_review.isnot(None),
            UserCard.last_review <= cutoff,
        )
        .count()
    )
    return count, count > 0


@router.get("/vocab", response_model=list[VocabOut])
def list_vocab(
    db: DbSession,
    user: CurrentUser,
    hsk_level: int | None = None,
    topic: str | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query = db.query(Vocabulary)
    if hsk_level is not None:
        query = query.filter(Vocabulary.hsk_level == hsk_level)
    if topic:
        query = query.filter(Vocabulary.topic == topic)
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


@router.get("/vocab/topics", response_model=list[VocabTopicOut])
def list_vocab_topics(db: DbSession, user: CurrentUser, hsk_level: int | None = None):
    query = db.query(Vocabulary.topic, func.count(Vocabulary.id)).filter(Vocabulary.topic.isnot(None))
    if hsk_level is not None:
        query = query.filter(Vocabulary.hsk_level == hsk_level)
    rows = query.group_by(Vocabulary.topic).order_by(func.count(Vocabulary.id).desc()).all()
    return [VocabTopicOut(topic=t, count=c) for t, c in rows]


@router.get("/cards/decks", response_model=DecksOut)
def list_decks(db: DbSession, user: CurrentUser):
    """HSK boxes → topic boxes with total/learned counts."""
    totals = (
        db.query(Vocabulary.hsk_level, Vocabulary.topic, func.count(Vocabulary.id))
        .filter(Vocabulary.topic.isnot(None), Vocabulary.hsk_level.in_((1, 2, 3)))
        .group_by(Vocabulary.hsk_level, Vocabulary.topic)
        .all()
    )
    learned_rows = (
        db.query(Vocabulary.hsk_level, Vocabulary.topic, func.count(UserCard.id))
        .join(UserCard, UserCard.vocab_id == Vocabulary.id)
        .filter(
            UserCard.user_id == user.id,
            UserCard.reps >= 1,
            Vocabulary.topic.isnot(None),
            Vocabulary.hsk_level.in_((1, 2, 3)),
        )
        .group_by(Vocabulary.hsk_level, Vocabulary.topic)
        .all()
    )
    learned_map = {(h, t): c for h, t, c in learned_rows}

    by_hsk: dict[int, list[DeckTopicOut]] = {1: [], 2: [], 3: []}
    hsk_totals = {1: 0, 2: 0, 3: 0}
    hsk_learned = {1: 0, 2: 0, 3: 0}
    for hsk, topic, total in totals:
        if hsk not in by_hsk:
            continue
        learned = int(learned_map.get((hsk, topic), 0))
        by_hsk[hsk].append(DeckTopicOut(topic=topic, total=int(total), learned=learned))
        hsk_totals[hsk] += int(total)
        hsk_learned[hsk] += learned

    for hsk in by_hsk:
        by_hsk[hsk].sort(key=lambda x: (-x.total, x.topic))

    learned_total = (
        db.query(UserCard).filter(UserCard.user_id == user.id, UserCard.reps >= 1).count()
    )
    daily_count, daily_ready = daily_review_stats(db, user.id)

    return DecksOut(
        hsk=[
            DeckHskOut(
                hsk_level=n,
                total=hsk_totals[n],
                learned=hsk_learned[n],
                topics=by_hsk[n],
            )
            for n in (1, 2, 3)
            if hsk_totals[n] > 0
        ],
        learned_total=learned_total,
        daily_review_ready=daily_ready,
        daily_review_count=min(5, daily_count) if daily_ready else 0,
    )


@router.get("/cards/learned", response_model=list[LearnedCardOut])
def learned_cards(
    db: DbSession,
    user: CurrentUser,
    hsk_level: int | None = None,
    topic: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = (
        db.query(UserCard)
        .join(UserCard.vocab)
        .options(contains_eager(UserCard.vocab))
        .filter(UserCard.user_id == user.id, UserCard.reps >= 1)
    )
    if hsk_level is not None:
        query = query.filter(Vocabulary.hsk_level == hsk_level)
    if topic:
        query = query.filter(Vocabulary.topic == topic)
    rows = (
        query.order_by(UserCard.last_review.desc().nullslast(), UserCard.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return rows


@router.get("/cards/daily-review", response_model=list[CardOut])
def daily_review_cards(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(5, ge=1, le=20),
):
    """Random sample of recently learned words eligible after ≥1 day."""
    cutoff = _daily_review_cutoff()
    pool = (
        db.query(UserCard)
        .options(joinedload(UserCard.vocab))
        .filter(
            UserCard.user_id == user.id,
            UserCard.reps >= 1,
            UserCard.last_review.isnot(None),
            UserCard.last_review <= cutoff,
        )
        .order_by(UserCard.last_review.desc())
        .limit(40)
        .all()
    )
    if not pool:
        return []
    k = min(limit, len(pool))
    return random.sample(pool, k)


@router.get("/cards/due", response_model=list[CardOut])
def due_cards(
    db: DbSession,
    user: CurrentUser,
    hsk_level: int | None = None,
    topic: str | None = None,
    limit: int = Query(20, ge=1, le=50),
):
    # Topic / HSK decks need more cards seeded so the set is not empty.
    ensure_limit = 100 if (topic or hsk_level is not None) else 30
    ensure_cards_for_user(
        db,
        user.id,
        limit=ensure_limit,
        hsk_level=hsk_level,
        topic=topic,
    )
    now = datetime.now(timezone.utc)
    filtered = topic or hsk_level is not None
    query = db.query(UserCard).filter(UserCard.user_id == user.id)
    if filtered:
        query = query.join(UserCard.vocab).options(contains_eager(UserCard.vocab))
        if hsk_level is not None:
            query = query.filter(Vocabulary.hsk_level == hsk_level)
        if topic:
            query = query.filter(Vocabulary.topic == topic)
    else:
        query = query.options(joinedload(UserCard.vocab))

    # Default queue: only due cards. Filtered decks: due first, then rest of set.
    if filtered:
        due = query.filter(UserCard.due <= now).order_by(UserCard.due).limit(limit).all()
        if len(due) >= limit:
            return due
        due_ids = {c.id for c in due}
        rest = (
            query.filter(UserCard.due > now)
            .order_by(UserCard.due)
            .limit(limit - len(due))
            .all()
        )
        return due + [c for c in rest if c.id not in due_ids]

    return query.filter(UserCard.due <= now).order_by(UserCard.due).limit(limit).all()


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
