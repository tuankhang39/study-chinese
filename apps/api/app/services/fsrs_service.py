from datetime import datetime, timezone

from fsrs import Card, Rating, Scheduler, State
from sqlalchemy.orm import Session

from app.models import UserCard, Vocabulary

RATING_MAP = {
    "again": Rating.Again,
    "hard": Rating.Hard,
    "good": Rating.Good,
    "easy": Rating.Easy,
}


def _scheduler() -> Scheduler:
    return Scheduler()


def card_from_model(model: UserCard) -> Card:
    due = model.due if model.due.tzinfo else model.due.replace(tzinfo=timezone.utc)
    last_review = model.last_review
    if last_review is not None and last_review.tzinfo is None:
        last_review = last_review.replace(tzinfo=timezone.utc)

    kwargs = {
        "card_id": model.id,
        "state": State(model.state) if model.state else State.Learning,
        "due": due,
        "last_review": last_review,
    }
    if model.stability:
        kwargs["stability"] = model.stability
    if model.difficulty:
        kwargs["difficulty"] = model.difficulty
    return Card(**kwargs)


def apply_card_to_model(model: UserCard, card: Card) -> None:
    model.state = int(card.state)
    model.stability = float(card.stability or 0.0)
    model.difficulty = float(card.difficulty or 0.0)
    model.due = card.due
    model.last_review = card.last_review


def ensure_cards_for_user(db: Session, user_id: int, limit: int = 50, hsk_max: int = 3) -> int:
    existing = {
        row[0]
        for row in db.query(UserCard.vocab_id).filter(UserCard.user_id == user_id).all()
    }
    vocab_q = (
        db.query(Vocabulary)
        .filter(Vocabulary.hsk_level <= hsk_max)
        .order_by(Vocabulary.hsk_level, Vocabulary.frequency.nulls_last(), Vocabulary.id)
    )
    created = 0
    now = datetime.now(timezone.utc)
    for vocab in vocab_q:
        if vocab.id in existing:
            continue
        db.add(
            UserCard(
                user_id=user_id,
                vocab_id=vocab.id,
                due=now,
                stability=0.0,
                difficulty=0.0,
                state=int(State.Learning),
            )
        )
        created += 1
        if created >= limit:
            break
    if created:
        db.commit()
    return created


def review_card(db: Session, model: UserCard, rating_key: str) -> UserCard:
    rating = RATING_MAP[rating_key]
    scheduler = _scheduler()
    if model.reps == 0 and not model.last_review:
        card = Card()
    else:
        card = card_from_model(model)
    reviewed, _log = scheduler.review_card(card, rating)
    model.reps += 1
    if rating == Rating.Again:
        model.lapses += 1
    apply_card_to_model(model, reviewed)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


DEFAULT_MISSIONS = [
    {"id": "learn_words", "title": "Học 10 từ mới", "xp": 20, "done": False, "target": 10, "progress": 0},
    {"id": "listen", "title": "Nghe 5 câu", "xp": 20, "done": False, "target": 5, "progress": 0},
    {"id": "roleplay", "title": "Nói với AI 1 tình huống", "xp": 30, "done": False, "target": 1, "progress": 0},
    {"id": "review", "title": "Ôn lại từ cũ", "xp": 20, "done": False, "target": 5, "progress": 0},
]


def get_or_create_mission(db: Session, user_id: int, today=None):
    from datetime import date
    import copy

    from app.models import DailyMission

    today = today or date.today()
    mission = (
        db.query(DailyMission)
        .filter(DailyMission.user_id == user_id, DailyMission.mission_date == today)
        .first()
    )
    if mission:
        return mission
    mission = DailyMission(
        user_id=user_id,
        mission_date=today,
        tasks=copy.deepcopy(DEFAULT_MISSIONS),
        completed=False,
        xp_awarded=0,
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission
