from fastapi import APIRouter, HTTPException

from app.deps import CurrentUser, DbSession, award_xp, touch_streak
from app.schemas import CompleteMissionTaskRequest, HomeOut, MissionOut, MissionTask, UserOut
from app.services.fsrs_service import ensure_cards_for_user, get_or_create_mission
from app.models import UserCard
from datetime import datetime, timezone

router = APIRouter(tags=["home"])


@router.get("/home", response_model=HomeOut)
def home(db: DbSession, user: CurrentUser) -> HomeOut:
    ensure_cards_for_user(db, user.id, limit=40)
    mission = get_or_create_mission(db, user.id)
    now = datetime.now(timezone.utc)
    due_count = (
        db.query(UserCard)
        .filter(UserCard.user_id == user.id, UserCard.due <= now)
        .count()
    )
    tip = (
        "Hôm nay hãy luyện Listening 5 phút — nghe yếu sẽ kéo chậm khi nói với sếp."
        if due_count < 5
        else f"Bạn có {due_count} thẻ đến hạn. Ôn nhanh trước khi học từ mới."
    )
    return HomeOut(
        user=UserOut.model_validate(user),
        mission=MissionOut(
            id=mission.id,
            mission_date=mission.mission_date,
            tasks=[MissionTask(**t) for t in mission.tasks],
            completed=mission.completed,
            xp_awarded=mission.xp_awarded,
        ),
        due_count=due_count,
        continue_track="hsk" if due_count else "work",
        tip=tip,
    )


@router.get("/missions/today", response_model=MissionOut)
def today_mission(db: DbSession, user: CurrentUser) -> MissionOut:
    mission = get_or_create_mission(db, user.id)
    return MissionOut(
        id=mission.id,
        mission_date=mission.mission_date,
        tasks=[MissionTask(**t) for t in mission.tasks],
        completed=mission.completed,
        xp_awarded=mission.xp_awarded,
    )


@router.post("/missions/today/complete-task", response_model=MissionOut)
def complete_task(body: CompleteMissionTaskRequest, db: DbSession, user: CurrentUser) -> MissionOut:
    mission = get_or_create_mission(db, user.id)
    tasks = list(mission.tasks or [])
    found = False
    awarded = 0
    for task in tasks:
        if task.get("id") != body.task_id:
            continue
        found = True
        was_done = bool(task.get("done"))
        task["progress"] = min(
            int(task.get("target", 1)),
            int(task.get("progress", 0)) + max(1, body.increment),
        )
        if task["progress"] >= int(task.get("target", 1)):
            task["done"] = True
            if not was_done:
                awarded = int(task.get("xp", 0))
        break
    if not found:
        raise HTTPException(status_code=404, detail="Task not found")
    mission.tasks = tasks
    touch_streak(user)
    if awarded:
        award_xp(db, user, awarded, f"mission:{body.task_id}")
        mission.xp_awarded += awarded
    if all(t.get("done") for t in tasks) and not mission.completed:
        mission.completed = True
        award_xp(db, user, 50, "perfect_day")
        mission.xp_awarded += 50
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return MissionOut(
        id=mission.id,
        mission_date=mission.mission_date,
        tasks=[MissionTask(**t) for t in mission.tasks],
        completed=mission.completed,
        xp_awarded=mission.xp_awarded,
    )
