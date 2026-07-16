"""Administração: gestão de usuários (criar/editar/senha/permissões) e dados
da organização. Restrito a papel admin/direção.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.security import hash_senha
from app.models.enums import PapelUsuario
from app.models.organizacao import Fazenda, Organizacao
from app.models.usuario import Usuario, UsuarioFazenda
from app.schemas import (
    OrganizacaoOut,
    OrganizacaoUpdateIn,
    SenhaResetIn,
    UsuarioAdminOut,
    UsuarioCreateIn,
    UsuarioUpdateIn,
)

router = APIRouter(prefix="/admin", tags=["admin"])

PAPEIS = {p.value for p in PapelUsuario}
VE_TODAS = (PapelUsuario.admin, PapelUsuario.direcao)  # papéis que enxergam todas as fazendas


def exigir_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.papel not in VE_TODAS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas administradores acessam esta área")
    return user


def _fazenda_ids(db: Session, usuario_id) -> list[uuid.UUID]:
    return list(db.execute(
        select(UsuarioFazenda.fazenda_id).where(UsuarioFazenda.usuario_id == usuario_id)
    ).scalars().all())


def _out(db: Session, u: Usuario) -> UsuarioAdminOut:
    return UsuarioAdminOut(
        id=u.id, nome=u.nome, email=u.email, papel=u.papel.value, ativo=u.ativo,
        fazenda_ids=_fazenda_ids(db, u.id),
    )


def _n_admins_ativos(db: Session, org_id, exceto=None) -> int:
    stmt = select(func.count(Usuario.id)).where(
        Usuario.org_id == org_id, Usuario.ativo.is_(True), Usuario.papel == PapelUsuario.admin
    )
    if exceto is not None:
        stmt = stmt.where(Usuario.id != exceto)
    return int(db.execute(stmt).scalar_one())


def _set_fazendas(db: Session, u: Usuario, fazenda_ids: list[uuid.UUID]) -> None:
    """Define o escopo de fazendas. admin/direção veem todas → sem vínculos."""
    db.execute(
        UsuarioFazenda.__table__.delete().where(UsuarioFazenda.usuario_id == u.id)
    )
    if u.papel in VE_TODAS:
        return
    validos = set(db.execute(
        select(Fazenda.id).where(Fazenda.org_id == u.org_id, Fazenda.id.in_(fazenda_ids or []))
    ).scalars().all())
    for fid in validos:
        db.add(UsuarioFazenda(usuario_id=u.id, fazenda_id=fid))


# ---------------- Usuários ----------------
@router.get("/usuarios", response_model=list[UsuarioAdminOut])
def listar_usuarios(
    db: Session = Depends(get_db), admin: Usuario = Depends(exigir_admin)
) -> list[UsuarioAdminOut]:
    usuarios = db.execute(
        select(Usuario).where(Usuario.org_id == admin.org_id).order_by(Usuario.nome)
    ).scalars().all()
    return [_out(db, u) for u in usuarios]


@router.post("/usuarios", response_model=UsuarioAdminOut, status_code=201)
def criar_usuario(
    body: UsuarioCreateIn, db: Session = Depends(get_db), admin: Usuario = Depends(exigir_admin)
) -> UsuarioAdminOut:
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email inválido")
    if body.papel not in PAPEIS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Papel inválido")
    if len(body.senha) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A senha deve ter ao menos 6 caracteres")
    existe = db.execute(select(Usuario).where(Usuario.email == email)).scalar_one_or_none()
    if existe:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um usuário com esse email")
    u = Usuario(
        org_id=admin.org_id, nome=body.nome.strip(), email=email,
        senha_hash=hash_senha(body.senha), papel=PapelUsuario(body.papel), ativo=True,
    )
    db.add(u)
    db.flush()
    _set_fazendas(db, u, body.fazenda_ids)
    db.commit()
    db.refresh(u)
    return _out(db, u)


def _get_usuario(usuario_id: uuid.UUID, db: Session, admin: Usuario) -> Usuario:
    u = db.get(Usuario, usuario_id)
    if u is None or u.org_id != admin.org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
    return u


@router.put("/usuarios/{usuario_id}", response_model=UsuarioAdminOut)
def editar_usuario(
    usuario_id: uuid.UUID, body: UsuarioUpdateIn,
    db: Session = Depends(get_db), admin: Usuario = Depends(exigir_admin),
) -> UsuarioAdminOut:
    u = _get_usuario(usuario_id, db, admin)
    novo_papel = PapelUsuario(body.papel) if body.papel is not None else u.papel
    if body.papel is not None and body.papel not in PAPEIS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Papel inválido")
    nova_ativo = body.ativo if body.ativo is not None else u.ativo

    # trava anti-lockout: não deixar o sistema sem nenhum admin ativo
    era_admin_ativo = u.papel == PapelUsuario.admin and u.ativo
    fica_admin_ativo = novo_papel == PapelUsuario.admin and nova_ativo
    if era_admin_ativo and not fica_admin_ativo and _n_admins_ativos(db, admin.org_id, exceto=u.id) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Precisa haver ao menos um administrador ativo")
    if u.id == admin.id and body.ativo is False:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Você não pode desativar a si mesmo")

    if body.nome is not None:
        u.nome = body.nome.strip()
    u.papel = novo_papel
    u.ativo = nova_ativo
    if body.fazenda_ids is not None or body.papel is not None:
        _set_fazendas(db, u, body.fazenda_ids if body.fazenda_ids is not None else _fazenda_ids(db, u.id))
    db.commit()
    db.refresh(u)
    return _out(db, u)


@router.put("/usuarios/{usuario_id}/senha", status_code=204)
def resetar_senha(
    usuario_id: uuid.UUID, body: SenhaResetIn,
    db: Session = Depends(get_db), admin: Usuario = Depends(exigir_admin),
) -> None:
    u = _get_usuario(usuario_id, db, admin)
    if len(body.senha) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A senha deve ter ao menos 6 caracteres")
    u.senha_hash = hash_senha(body.senha)
    db.commit()


@router.delete("/usuarios/{usuario_id}", status_code=204)
def excluir_usuario(
    usuario_id: uuid.UUID, db: Session = Depends(get_db), admin: Usuario = Depends(exigir_admin)
) -> None:
    u = _get_usuario(usuario_id, db, admin)
    if u.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Você não pode excluir a si mesmo")
    if u.papel == PapelUsuario.admin and u.ativo and _n_admins_ativos(db, admin.org_id, exceto=u.id) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Precisa haver ao menos um administrador ativo")
    db.delete(u)
    db.commit()


# ---------------- Organização ----------------
@router.get("/organizacao", response_model=OrganizacaoOut)
def obter_organizacao(
    db: Session = Depends(get_db), admin: Usuario = Depends(exigir_admin)
) -> Organizacao:
    return db.get(Organizacao, admin.org_id)


@router.put("/organizacao", response_model=OrganizacaoOut)
def editar_organizacao(
    body: OrganizacaoUpdateIn, db: Session = Depends(get_db), admin: Usuario = Depends(exigir_admin)
) -> Organizacao:
    org = db.get(Organizacao, admin.org_id)
    if not body.nome.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Informe o nome da organização")
    org.nome = body.nome.strip()
    db.commit()
    db.refresh(org)
    return org
