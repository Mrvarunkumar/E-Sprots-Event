"""
╔══════════════════════════════════════════════════════════════════╗
║       APEX ARENA — E-Sports Event Backend                        ║
║       FastAPI + Supabase                                         ║
║       Run: uvicorn main:app --host 127.0.0.1 --port 8000 --reload  ║
╚══════════════════════════════════════════════════════════════════╝
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from config import settings
from routers import registration, admin, export, pdf as pdf_router


# ─── LIFESPAN ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🎮  Apex Arena backend starting up …")
    print(f"    ENV:         {settings.app_env}")
    print(f"    Supabase:    {settings.supabase_url}")
    print(f"    CORS origins:{settings.cors_origins}")
    yield
    print("🛑  Apex Arena backend shutting down.")


# ─── APP ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Apex Arena — E-Sports Event API",
    description=(
        "Backend for the Apex Arena E-Sports Event hosted by VTU Kalburagi.\n\n"
        "Handles team registration, admin dashboard, Excel exports, and PDF generation."
    ),
    version="1.0.0",
    contact={
        "name": "Apex Arena Team",
        "email": "admin@apexarena.in",
    },
    license_info={"name": "MIT"},
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── ROUTERS ─────────────────────────────────────────────────────────────────
app.include_router(registration.router)   # /api/register, /api/counts
app.include_router(admin.router)          # /admin/*
app.include_router(export.router)         # /export/*
app.include_router(pdf_router.router)     # /download-pdf


# ─── SERVE FRONTEND ─────────────────
frontend_path = os.path.join(os.path.dirname(__file__), "..", "forntend")
if os.path.isdir(frontend_path):
    app.mount(
        "/forntend",
        StaticFiles(directory=frontend_path, html=True),
        name="frontend",
    )


# ─── ROOT REDIRECT ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    # Redirect localhost:8000 straight to the website homepage!
    return RedirectResponse(url="/forntend/index.html")


@app.get("/health", tags=["Health"])
async def health():
    """Lightweight health probe for deployment platforms."""
    return {"status": "ok"}


# ─── GLOBAL EXCEPTION HANDLER ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected server error occurred.",
            "detail":  str(exc) if settings.app_env == "development" else "Internal server error",
        },
    )


# ─── RUN (dev only) ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
