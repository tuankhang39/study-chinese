import random

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import joinedload

from app.core.config import ai_limit_for_plan

from app.deps import CurrentUser, DbSession, award_xp, touch_streak
from app.models import RoleplaySession, Scenario, Vocabulary
from app.schemas import (
    ListeningItemOut,
    RoleplayCreateRequest,
    RoleplayMessageRequest,
    RoleplaySessionOut,
    ScenarioOut,
    VocabOut,
)
from app.services.ai_service import generate_roleplay_turn
from app.services.fsrs_service import get_or_create_mission
from datetime import date

router = APIRouter(tags=["learn"])


@router.get("/scenarios", response_model=list[ScenarioOut])
def list_scenarios(
    db: DbSession,
    user: CurrentUser,
    track: str | None = "work",
    job_tag: str | None = None,
):
    q = db.query(Scenario)
    if track:
        q = q.filter(Scenario.track == track)
    if job_tag:
        q = q.filter(Scenario.job_tag == job_tag)
    return q.order_by(Scenario.id).all()


@router.post("/roleplay/sessions", response_model=RoleplaySessionOut)
def create_session(body: RoleplayCreateRequest, db: DbSession, user: CurrentUser):
    scenario = db.get(Scenario, body.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    starter = ""
    if scenario.starter_lines:
        starter = scenario.starter_lines[0] if isinstance(scenario.starter_lines[0], str) else scenario.starter_lines[0].get("zh", "")
    messages = [
        {
            "role": "assistant",
            "zh": starter or "你好，我们开始吧。",
            "vi": "Xin chào, chúng ta bắt đầu nhé.",
        }
    ]
    session = RoleplaySession(
        user_id=user.id,
        scenario_id=scenario.id,
        messages=messages,
        scores=None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/roleplay/sessions/{session_id}/message", response_model=RoleplaySessionOut)
async def send_message(
    session_id: int,
    body: RoleplayMessageRequest,
    db: DbSession,
    user: CurrentUser,
):
    session = (
        db.query(RoleplaySession)
        .options(joinedload(RoleplaySession.scenario))
        .filter(RoleplaySession.id == session_id, RoleplaySession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    today = date.today()
    if user.ai_messages_date != today:
        user.ai_messages_date = today
        user.ai_messages_today = 0
    limit = ai_limit_for_plan(getattr(user, "plan", None) or "free")
    if limit is not None and user.ai_messages_today >= limit:
        raise HTTPException(status_code=429, detail="Daily AI message limit reached")

    history = []
    for m in session.messages:
        role = m.get("role", "assistant")
        content = m.get("zh") or m.get("content") or ""
        history.append({"role": "assistant" if role == "assistant" else "user", "content": content})

    result = await generate_roleplay_turn(
        system_prompt=session.scenario.prompt_system,
        history=history,
        user_message=body.message,
    )

    messages = list(session.messages)
    messages.append({"role": "user", "zh": body.message, "vi": ""})
    messages.append(
        {
            "role": "assistant",
            "zh": result.get("reply_zh", "好的。"),
            "vi": result.get("reply_vi", ""),
        }
    )
    session.messages = messages
    session.scores = {
        "grammar": result.get("grammar"),
        "vocabulary": result.get("vocabulary"),
        "naturalness": result.get("naturalness"),
        "corrected_zh": result.get("corrected_zh"),
        "corrected_vi": result.get("corrected_vi"),
        "feedback_vi": result.get("feedback_vi"),
    }
    user.ai_messages_today += 1
    touch_streak(user)
    award_xp(db, user, 10, "roleplay_message")

    mission = get_or_create_mission(db, user.id)
    tasks = list(mission.tasks or [])
    for task in tasks:
        if task.get("id") == "roleplay" and not task.get("done"):
            task["progress"] = int(task.get("progress", 0)) + 1
            if task["progress"] >= int(task.get("target", 1)):
                task["done"] = True
                award_xp(db, user, int(task.get("xp", 30)), "mission:roleplay")
                mission.xp_awarded += int(task.get("xp", 30))
            break
    mission.tasks = tasks
    if all(t.get("done") for t in tasks) and not mission.completed:
        mission.completed = True
        award_xp(db, user, 50, "perfect_day")
        mission.xp_awarded += 50
    db.add(mission)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/listening/next", response_model=ListeningItemOut)
def listening_next(
    db: DbSession,
    user: CurrentUser,
    hsk_level: int | None = Query(None),
):
    q = db.query(Vocabulary)
    if hsk_level is not None:
        q = q.filter(Vocabulary.hsk_level == hsk_level)
    else:
        q = q.filter(Vocabulary.hsk_level <= 3)
    pool = q.order_by(Vocabulary.id).limit(400).all()
    if len(pool) < 4:
        raise HTTPException(status_code=400, detail="Not enough vocabulary seeded")
    answer = random.choice(pool)
    distractors = random.sample([v for v in pool if v.id != answer.id], 3)
    options = [answer.meaning_vi] + [d.meaning_vi for d in distractors]
    random.shuffle(options)
    return ListeningItemOut(
        vocab=VocabOut.model_validate(answer),
        options=options,
        answer_index=options.index(answer.meaning_vi),
    )


@router.post("/listening/complete")
def listening_complete(db: DbSession, user: CurrentUser, correct: bool = True):
    touch_streak(user)
    award_xp(db, user, 5 if correct else 1, "listening")
    mission = get_or_create_mission(db, user.id)
    tasks = list(mission.tasks or [])
    for task in tasks:
        if task.get("id") == "listen" and not task.get("done"):
            task["progress"] = int(task.get("progress", 0)) + 1
            if task["progress"] >= int(task.get("target", 1)):
                task["done"] = True
                award_xp(db, user, int(task.get("xp", 20)), "mission:listen")
                mission.xp_awarded += int(task.get("xp", 20))
            break
    mission.tasks = tasks
    if all(t.get("done") for t in tasks) and not mission.completed:
        mission.completed = True
        award_xp(db, user, 50, "perfect_day")
        mission.xp_awarded += 50
    db.add(mission)
    db.commit()
    return {"ok": True, "xp": user.xp, "streak": user.streak}
