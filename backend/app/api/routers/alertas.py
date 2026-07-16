import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import fazendas_do_usuario, get_current_user, get_fazenda_no_escopo
from app.models.enums import StatusAlerta
from app.models.gatilho import Alerta
from app.models.usuario import Usuario
from app.schemas import AlertaOut
from app.services.gatilhos import sincronizar_alertas

router = APIRouter(prefix="/alertas", tags=["alertas"])


@router.get("", response_model=list[AlertaOut])
def listar_alertas(
    apenas_abertos: bool = True,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> list[AlertaOut]:
    """Alertas de todas as fazendas no escopo do usuario, mais severos primeiro."""
    fazendas = fazendas_do_usuario(db, user)
    ids = [f.id for f in fazendas]
    if not ids:
        return []
    stmt = select(Alerta).where(Alerta.fazenda_id.in_(ids))
    if apenas_abertos:
        stmt = stmt.where(Alerta.status == StatusAlerta.aberto)
    stmt = stmt.order_by(Alerta.avaliado_em.desc())
    return list(db.execute(stmt).scalars().all())


@router.post("/reavaliar/{fazenda_id}", response_model=list[AlertaOut])
def reavaliar_fazenda(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> list[AlertaOut]:
    """Roda o motor de gatilhos para a fazenda e retorna os alertas abertos resultantes."""
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    sincronizar_alertas(db, faz)
    return list(
        db.execute(
            select(Alerta)
            .where(Alerta.fazenda_id == faz.id, Alerta.status == StatusAlerta.aberto)
            .order_by(Alerta.avaliado_em.desc())
        ).scalars().all()
    )
