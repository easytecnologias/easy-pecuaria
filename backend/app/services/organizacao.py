"""Criação de novas organizações (tenants) — onboarding de cliente SaaS.
Cria a org + o primeiro admin dela + semeia as regras de gatilho (o catálogo de
indicadores é global; as premissas/metas são semeadas por fazenda em criar_fazenda).
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_senha
from app.models.enums import PapelUsuario
from app.models.gatilho import RegraGatilho
from app.models.indicador import IndicadorDefinicao
from app.models.organizacao import Organizacao
from app.models.usuario import Usuario


def slugify(texto: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", texto.strip().lower()).strip("-")
    return s or "org"


def _semear_regras(db: Session, org_id) -> None:
    from app.seed.seed import REGRAS  # import tardio: evita ciclo e efeitos colaterais

    inds = {i.codigo: i for i in db.execute(select(IndicadorDefinicao)).scalars().all()}
    for (cod, nome, op, tipo, vfix, pchave, tol, sev, acao) in REGRAS:
        ind = inds.get(cod)
        if ind is None:
            continue
        db.add(RegraGatilho(
            org_id=org_id, indicador_id=ind.id, nome=nome, operador=op,
            tipo_referencia=tipo, valor_referencia=vfix, parametro_chave=pchave,
            tolerancia=tol, severidade=sev, acao=acao,
        ))


def criar_organizacao(
    db: Session, nome: str, slug: str,
    admin_nome: str, admin_email: str, admin_senha: str,
) -> tuple[Organizacao, Usuario]:
    org = Organizacao(nome=nome.strip(), slug=slug)
    db.add(org)
    db.flush()

    admin = Usuario(
        org_id=org.id, nome=admin_nome.strip(), email=admin_email.strip().lower(),
        senha_hash=hash_senha(admin_senha), papel=PapelUsuario.admin,
        ativo=True, is_superadmin=False,
    )
    db.add(admin)
    _semear_regras(db, org.id)
    db.commit()
    db.refresh(org)
    db.refresh(admin)
    return org, admin
