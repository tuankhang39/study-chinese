"""One-shot seed structured HSK1 inside API container / local."""
from unittest.mock import MagicMock

from app.core.database import Base, SessionLocal, engine
from app.models import Course, Lesson, LessonItem, LessonStep
from app.routers.curriculum import admin_seed_hsk1

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        r = admin_seed_hsk1(MagicMock(), db, replace=True)
        print(r)
        print("courses", db.query(Course).count())
        print("lessons", db.query(Lesson).count())
        print("steps", db.query(LessonStep).count())
        print("items", db.query(LessonItem).count())
    finally:
        db.close()
