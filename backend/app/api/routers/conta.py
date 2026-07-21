import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.financeiro import (
    STATUS_CONTA,
    TIPOS_CONTA,
    TIPOS_DOCUMENTO,
    ContaFinanceira,
)
from app.models.usuario import Usuario
from app.schemas import BaixaIn, ContaIn, ContaOut, ResumoContas
from app.services.conta import baixar, resumo, situacao

router = APIRouter(tags=["contas"])


@router.get("/contas/opcoes")
def opcoes(user: Usuario = Depends(get_current_user)) -> dict:
    return {
        "tipos": list(TIPOS_CONTA),
        "documentos": list(TIPOS_DOCUMENTO),
        "status": list(STATUS_CONTA),
    }


def _out(c: ContaFinanceira) -> ContaOut:
    from datetime import date

    return ContaOut(
        id=c.id, tipo=c.tipo, descricao=c.descricao, categoria=c.categoria,
        contraparte=c.contraparte, documento=c.documento,
        numero_documento=c.numero_documento, valor=float(c.valor),
        emissao=c.emissao, vencimento=c.vencimento, status=c.status,
        situacao=situacao(c), dias=(c.vencimento - date.today()).days,
        data_baixa=c.data_baixa,
        valor_pago=float(c.valor_pago) if c.valor_pago is not None else None,
        observacao=c.observacao,
    )


@router.get("/fazendas/{fazenda_id}/contas", response_model=ResumoContas)
def listar_contas(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ResumoContas:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    return ResumoContas.model_validate(resumo(db, faz))


@router.post("/fazendas/{fazenda_id}/contas", response_model=ContaOut, status_code=201)
def nova_conta(
    fazenda_id: uuid.UUID,
    body: ContaIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ContaOut:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    if body.tipo not in TIPOS_CONTA:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"tipo invalido (use: {', '.join(TIPOS_CONTA)})"
        )
    if body.documento not in TIPOS_DOCUMENTO:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"documento invalido (use: {', '.join(TIPOS_DOCUMENTO)})",
        )
    if body.valor <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "O valor precisa ser maior que zero")

    c = ContaFinanceira(
        fazenda_id=faz.id, criado_por_nome=user.nome, **body.model_dump()
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _out(c)


def _conta_no_escopo(conta_id: uuid.UUID, db: Session, user: Usuario) -> ContaFinanceira:
    c = db.get(ContaFinanceira, conta_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conta nao encontrada")
    get_fazenda_no_escopo(c.fazenda_id, db, user)
    return c


@router.put("/contas/{conta_id}", response_model=ContaOut)
def editar_conta(
    conta_id: uuid.UUID,
    body: ContaIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ContaOut:
    c = _conta_no_escopo(conta_id, db, user)
    if c.status == "baixado":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Conta ja baixada — cancele a baixa antes de editar",
        )
    for campo, valor in body.model_dump().items():
        setattr(c, campo, valor)
    db.commit()
    db.refresh(c)
    return _out(c)


@router.post("/contas/{conta_id}/baixar", response_model=ContaOut)
def baixar_conta(
    conta_id: uuid.UUID,
    body: BaixaIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ContaOut:
    """Marca como paga/recebida e lanca o valor no caixa."""
    c = _conta_no_escopo(conta_id, db, user)
    faz = get_fazenda_no_escopo(c.fazenda_id, db, user)
    return _out(baixar(db, faz, c, body.data_baixa, body.valor_pago))


@router.delete("/contas/{conta_id}", status_code=204)
def excluir_conta(
    conta_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    c = _conta_no_escopo(conta_id, db, user)
    db.delete(c)
    db.commit()
