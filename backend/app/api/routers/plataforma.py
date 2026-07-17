"""Plataforma: gestão de organizações (tenants) pelo super-admin.
Onboarding de novos clientes, isolados entre si. Restrito a is_superadmin.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.organizacao import Fazenda, Organizacao
from app.models.usuario import Usuario
from app.schemas import OrgCreateIn, OrgPlataformaOut, OrgRenomearIn
from app.services.auditoria import registrar_audit
from app.services.organizacao import criar_organizacao, slugify

router = APIRouter(prefix="/platform", tags=["plataforma"])


def exigir_superadmin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if not user.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas o super-admin da plataforma")
    return user


def _out(db: Session, org: Organizacao) -> OrgPlataformaOut:
    n_faz = int(db.execute(
        select(func.count(Fazenda.id)).where(Fazenda.org_id == org.id)
    ).scalar_one())
    n_usr = int(db.execute(
        select(func.count(Usuario.id)).where(Usuario.org_id == org.id)
    ).scalar_one())
    return OrgPlataformaOut(id=org.id, nome=org.nome, slug=org.slug, n_fazendas=n_faz, n_usuarios=n_usr)


@router.get("/organizacoes", response_model=list[OrgPlataformaOut])
def listar_orgs(
    db: Session = Depends(get_db), sa: Usuario = Depends(exigir_superadmin)
) -> list[OrgPlataformaOut]:
    orgs = db.execute(select(Organizacao).order_by(Organizacao.nome)).scalars().all()
    return [_out(db, o) for o in orgs]


@router.post("/organizacoes", response_model=OrgPlataformaOut, status_code=201)
def nova_org(
    body: OrgCreateIn, db: Session = Depends(get_db), sa: Usuario = Depends(exigir_superadmin)
) -> OrgPlataformaOut:
    nome = body.nome.strip()
    if not nome:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Informe o nome da organização")
    slug = slugify(body.slug or body.nome)
    if db.execute(select(Organizacao).where(Organizacao.slug == slug)).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, f"Já existe organização com o slug '{slug}'")
    email = body.admin_email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email do admin inválido")
    if db.execute(select(Usuario).where(Usuario.email == email)).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um usuário com esse email")
    if len(body.admin_senha) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A senha do admin deve ter ao menos 6 caracteres")
    if not body.admin_nome.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Informe o nome do admin")

    org, _admin = criar_organizacao(db, nome, slug, body.admin_nome, email, body.admin_senha)
    registrar_audit(db, sa, "criar_organizacao", "organizacao", org.id, f"{org.nome} (admin {email})", org_id=org.id)
    return _out(db, org)


@router.put("/organizacoes/{org_id}", response_model=OrgPlataformaOut)
def renomear_org(
    org_id: uuid.UUID, body: OrgRenomearIn,
    db: Session = Depends(get_db), sa: Usuario = Depends(exigir_superadmin),
) -> OrgPlataformaOut:
    org = db.get(Organizacao, org_id)
    if org is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organização não encontrada")
    if not body.nome.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Informe o nome")
    org.nome = body.nome.strip()
    db.commit()
    db.refresh(org)
    registrar_audit(db, sa, "renomear_organizacao", "organizacao", org.id, org.nome, org_id=org.id)
    return _out(db, org)
