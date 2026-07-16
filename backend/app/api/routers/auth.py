from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.security import criar_token, verificar_senha
from app.models.usuario import Usuario
from app.schemas import TokenOut, UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> TokenOut:
    """Login via form (username = email). Retorna JWT."""
    user = db.execute(
        select(Usuario).where(Usuario.email == form.username)
    ).scalar_one_or_none()
    if not user or not verificar_senha(form.password, user.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou senha invalidos")
    if not user.ativo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuario inativo")
    token = criar_token(str(user.id), {"papel": user.papel.value, "org": str(user.org_id)})
    return TokenOut(access_token=token)


@router.get("/me", response_model=UsuarioOut)
def me(user: Usuario = Depends(get_current_user)) -> Usuario:
    return user
