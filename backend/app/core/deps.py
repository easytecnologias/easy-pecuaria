import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decodificar_token
from app.models.enums import PapelUsuario
from app.models.organizacao import Fazenda
from app.models.usuario import Usuario, UsuarioFazenda

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2), db: Session = Depends(get_db)
) -> Usuario:
    payload = decodificar_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido")
    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido") from exc
    user = db.get(Usuario, user_id)
    if not user or not user.ativo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario inativo ou inexistente")
    return user


def fazendas_do_usuario(db: Session, user: Usuario) -> list[Fazenda]:
    """Escopo multi-fazenda: admin/direcao veem todas da org; demais so as vinculadas."""
    stmt = select(Fazenda).where(Fazenda.org_id == user.org_id, Fazenda.ativo.is_(True))
    if user.papel not in (PapelUsuario.admin, PapelUsuario.direcao):
        stmt = stmt.join(
            UsuarioFazenda, UsuarioFazenda.fazenda_id == Fazenda.id
        ).where(UsuarioFazenda.usuario_id == user.id)
    return list(db.execute(stmt.order_by(Fazenda.nome)).scalars().all())


def get_fazenda_no_escopo(
    fazenda_id: uuid.UUID, db: Session, user: Usuario
) -> Fazenda:
    """Carrega uma fazenda garantindo que pertence ao escopo do usuario."""
    faz = db.get(Fazenda, fazenda_id)
    if not faz or faz.org_id != user.org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fazenda nao encontrada")
    if user.papel not in (PapelUsuario.admin, PapelUsuario.direcao):
        vinc = db.get(UsuarioFazenda, {"usuario_id": user.id, "fazenda_id": faz.id})
        if not vinc:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Sem acesso a esta fazenda")
    return faz
