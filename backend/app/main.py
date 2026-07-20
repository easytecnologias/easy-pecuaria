from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routers import (
    admin,
    alertas,
    auth,
    dashboard,
    desmame,
    escore,
    estoque,
    fazendas,
    financeiro,
    indicadores,
    inventario,
    mercado,
    movimento,
    nutricao,
    parto,
    plataforma,
    rebanho,
    reproducao,
    sanitario,
)
from app.core.config import settings
from app.core.db import engine

app = FastAPI(
    title="Pecuaria API",
    description="Backend do sistema de gestao pecuaria (multi-fazenda) — painel + motor de gatilhos.",
    version="0.1.0",
    # documentação oculta em produção (evita expor o mapa da API)
    docs_url="/docs" if settings.expose_docs else None,
    redoc_url="/redoc" if settings.expose_docs else None,
    openapi_url="/openapi.json" if settings.expose_docs else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(plataforma.router)
app.include_router(fazendas.router)
app.include_router(dashboard.router)
app.include_router(alertas.router)
app.include_router(indicadores.router)
app.include_router(rebanho.router)
app.include_router(reproducao.router)
app.include_router(estoque.router)
app.include_router(financeiro.router)
app.include_router(escore.router)
app.include_router(nutricao.router)
app.include_router(mercado.router)
app.include_router(sanitario.router)
app.include_router(movimento.router)
app.include_router(parto.router)
app.include_router(inventario.router)
app.include_router(desmame.router)


@app.get("/health", tags=["infra"])
def health() -> dict:
    """Liveness + checa conexao com o banco."""
    db_ok = True
    detail = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
    except Exception as exc:  # noqa: BLE001
        db_ok = False
        detail = str(exc)
    return {"status": "ok" if db_ok else "degraded", "database": db_ok, "detail": detail}
