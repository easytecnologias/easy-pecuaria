from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.security import criar_token, hash_senha, verificar_senha
from app.models.usuario import Usuario
from app.schemas import TokenOut, TrocarSenhaIn, UsuarioOut
from app.services.auditoria import registrar_audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _token(user: Usuario) -> str:
    return criar_token(str(user.id), {"papel": user.papel.value, "org": str(user.org_id)})


@router.post("/login", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> TokenOut:
    """Login via form (username = email). Retorna JWT."""
    user = db.execute(
        select(Usuario).where(Usuario.email == form.username.strip().lower())
    ).scalar_one_or_none()
    if not user or not verificar_senha(form.password, user.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou senha invalidos")
    if not user.ativo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuario inativo")
    registrar_audit(db, user, "login")
    return TokenOut(access_token=_token(user))


@router.post("/refresh", response_model=TokenOut)
def refresh(user: Usuario = Depends(get_current_user)) -> TokenOut:
    """Renova o token do usuário logado (sessão deslizante)."""
    return TokenOut(access_token=_token(user))


@router.put("/senha", status_code=204)
def trocar_minha_senha(
    body: TrocarSenhaIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    """Auto-serviço: o próprio usuário troca a sua senha."""
    if not verificar_senha(body.senha_atual, user.senha_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Senha atual incorreta")
    if len(body.senha_nova) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A nova senha deve ter ao menos 6 caracteres")
    if body.senha_nova == body.senha_atual:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A nova senha deve ser diferente da atual")
    user.senha_hash = hash_senha(body.senha_nova)
    db.commit()
    registrar_audit(db, user, "trocar_propria_senha")


@router.get("/me", response_model=UsuarioOut)
def me(user: Usuario = Depends(get_current_user)) -> Usuario:
    return user
