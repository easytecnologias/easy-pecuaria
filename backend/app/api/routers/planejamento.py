import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.planejamento import (
    PERIODOS,
    STATUS_ATIVIDADE,
    TIPOS_ATIVIDADE,
    Atividade,
)
from app.models.usuario import Usuario
from app.schemas import (
    AtividadeIn,
    AtividadeOut,
    AtividadeUpdateIn,
    ConcluirAtividadeIn,
    ResumoPlanejamento,
)
from app.services.planejamento import concluir, criar, resumo

router = APIRouter(tags=["planejamento"])


@router.get("/planejamento/opcoes")
def opcoes(user: Usuario = Depends(get_current_user)) -> dict:
    return {"periodos": list(PERIODOS), "tipos": list(TIPOS_ATIVIDADE), "status": list(STATUS_ATIVIDADE)}


@router.get("/fazendas/{fazenda_id}/planejamento", response_model=ResumoPlanejamento)
def listar_planejamento(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ResumoPlanejamento:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    r = resumo(db, faz, user)
    return ResumoPlanejamento(
        **{k: v for k, v in r.items() if k != "atividades"},
        atividades=[AtividadeOut.model_validate(a) for a in r["atividades"]],
    )


@router.post("/fazendas/{fazenda_id}/planejamento", response_model=AtividadeOut, status_code=201)
def nova_atividade(
    fazenda_id: uuid.UUID,
    body: AtividadeIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Atividade:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    if body.periodo not in PERIODOS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"periodo invalido (use: {', '.join(PERIODOS)})")
    if body.tipo not in TIPOS_ATIVIDADE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"tipo invalido (use: {', '.join(TIPOS_ATIVIDADE)})")
    return criar(db, faz, body.model_dump(), user)


def _atividade_no_escopo(ativ_id: uuid.UUID, db: Session, user: Usuario) -> Atividade:
    a = db.get(Atividade, ativ_id)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Atividade nao encontrada")
    get_fazenda_no_escopo(a.fazenda_id, db, user)
    return a


@router.put("/planejamento/{ativ_id}", response_model=AtividadeOut)
def editar_atividade(
    ativ_id: uuid.UUID,
    body: AtividadeUpdateIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Atividade:
    a = _atividade_no_escopo(ativ_id, db, user)
    dados = body.model_dump(exclude_unset=True)
    if dados.get("status") and dados["status"] not in STATUS_ATIVIDADE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "status invalido")
    if "responsavel_id" in dados:
        resp = db.get(Usuario, dados["responsavel_id"]) if dados["responsavel_id"] else None
        a.responsavel_nome = resp.nome if resp else None
    for campo, valor in dados.items():
        setattr(a, campo, valor)
    db.commit()
    db.refresh(a)
    return a


@router.post("/planejamento/{ativ_id}/concluir", response_model=AtividadeOut)
def concluir_atividade(
    ativ_id: uuid.UUID,
    body: ConcluirAtividadeIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Atividade:
    a = _atividade_no_escopo(ativ_id, db, user)
    if a.status == "concluida":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Atividade ja concluida")
    return concluir(db, a, user, body.observacao)


@router.delete("/planejamento/{ativ_id}", status_code=204)
def excluir_atividade(
    ativ_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    a = _atividade_no_escopo(ativ_id, db, user)
    db.delete(a)
    db.commit()
