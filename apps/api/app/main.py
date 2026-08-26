from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import admin, admin_manage, auth, curriculum, learn, missions, vocab

app = FastAPI(title="Tiếng Trung đi làm API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(vocab.router, prefix="/api")
app.include_router(missions.router, prefix="/api")
app.include_router(learn.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(admin_manage.router, prefix="/api")
app.include_router(curriculum.router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}
