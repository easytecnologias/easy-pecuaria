import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.security import criar_token, hash_senha, senha_fraca, verificar_senha
from app.models.usuario import Usuario
from app.schemas import TokenOut, TrocarSenhaIn, UsuarioOut
from app.services.auditoria import registrar_audit

router = APIRouter(prefix="/auth", tags=["auth"])

# rate-limiting simples em memória: trava força-bruta por (ip + email)
_LIMITE = 10           # tentativas falhas permitidas
_JANELA = 900          # dentro de 15 min
_falhas: dict[str, list[float]] = {}


def _ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "?"


def _rate_key(request: Request, username: str) -> str:
    return f"{_ip(request)}|{username.strip().lower()}"


def _checar_bloqueio(key: str) -> None:
    agora = time.time()
    tent = [t for t in _falhas.get(key, []) if agora - t < _JANELA]
    _falhas[key] = tent
    if len(tent) >= _LIMITE:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Muitas tentativas de login. Aguarde alguns minutos e tente de novo.",
        )


def _registrar_falha(key: str) -> None:
    _falhas.setdefault(key, []).append(time.time())


def _token(user: Usuario) -> str:
    return criar_token(str(user.id), {"papel": user.papel.value, "org": str(user.org_id)})


@router.post("/login", response_model=TokenOut)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenOut:
    """Login via form (username = email). Retorna JWT. Protegido contra força-bruta."""
    key = _rate_key(request, form.username)
    _checar_bloqueio(key)
    user = db.execute(
        select(Usuario).where(Usuario.email == form.username.strip().lower())
    ).scalar_one_or_none()
    if not user or not verificar_senha(form.password, user.senha_hash):
        _registrar_falha(key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou senha invalidos")
    if not user.ativo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuario inativo")
    _falhas.pop(key, None)  # sucesso zera o contador
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
    if senha_fraca(body.senha_nova):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A nova senha deve ter ao menos 8 caracteres")
    if body.senha_nova == body.senha_atual:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A nova senha deve ser diferente da atual")
    user.senha_hash = hash_senha(body.senha_nova)
    db.commit()
    registrar_audit(db, user, "trocar_propria_senha")


@router.get("/me", response_model=UsuarioOut)
def me(user: Usuario = Depends(get_current_user)) -> Usuario:
    return user
