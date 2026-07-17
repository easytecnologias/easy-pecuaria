"""Trilha de auditoria: registrar ações sensíveis. Best-effort — nunca deve
quebrar a operação principal (usa transação própria e engole erros)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.auditoria import AuditLog
from app.models.usuario import Usuario


def registrar_audit(
    db: Session, usuario: Usuario, acao: str,
    entidade: str | None = None, entidade_id=None, detalhe: str | None = None,
    org_id=None,
) -> None:
    try:
        db.add(AuditLog(
            org_id=org_id if org_id is not None else usuario.org_id,
            usuario_id=usuario.id, usuario_email=usuario.email,
            acao=acao, entidade=entidade, entidade_id=entidade_id,
            detalhe=(detalhe[:300] if detalhe else None),
        ))
        db.commit()
    except Exception:
        db.rollback()
