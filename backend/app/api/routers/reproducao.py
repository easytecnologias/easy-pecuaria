import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.rebanho import Animal
from app.models.reproducao import Inseminacao
from app.models.usuario import Usuario
from app.schemas import (
    DGIn,
    GrupoReproducao,
    InseminacaoIn,
    InseminacaoOut,
    InseminacaoUpdateIn,
    ResumoReproducao,
)
from app.services.reproducao import (
    recomputar_taxa_prenhez,
    registrar_dg,
    registrar_inseminacao,
    resumo_reproducao,
)

router = APIRouter(tags=["reproducao"])


def _out(ins: Inseminacao, brinco: str) -> InseminacaoOut:
    return InseminacaoOut(
        id=ins.id, animal_id=ins.animal_id, animal_brinco=brinco, data=ins.data,
        touro=ins.touro, inseminador=ins.inseminador, protocolo=ins.protocolo,
        resultado=ins.resultado, dg_data=ins.dg_data,
    )


def _get_ins_no_escopo(ins_id: uuid.UUID, db: Session, user: Usuario) -> Inseminacao:
    ins = db.get(Inseminacao, ins_id)
    if ins is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inseminação não encontrada")
    get_fazenda_no_escopo(ins.fazenda_id, db, user)
    return ins


@router.get("/fazendas/{fazenda_id}/reproducao", response_model=ResumoReproducao)
def resumo(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ResumoReproducao:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    agg = resumo_reproducao(db, faz)
    linhas = db.execute(
        select(Inseminacao, Animal.brinco)
        .join(Animal, Animal.id == Inseminacao.animal_id)
        .where(Inseminacao.fazenda_id == faz.id)
        .order_by(Inseminacao.data.desc())
    ).all()
    return ResumoReproducao(
        total=agg["total"], prenhes=agg["prenhes"], vazias=agg["vazias"],
        pendentes=agg["pendentes"], taxa_prenhez=agg["taxa_prenhez"],
        por_touro=[GrupoReproducao(**g) for g in agg["por_touro"]],
        por_inseminador=[GrupoReproducao(**g) for g in agg["por_inseminador"]],
        inseminacoes=[_out(i, brinco) for i, brinco in linhas],
    )


@router.post("/fazendas/{fazenda_id}/inseminacoes", response_model=InseminacaoOut, status_code=201)
def nova_inseminacao(
    fazenda_id: uuid.UUID,
    body: InseminacaoIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> InseminacaoOut:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    animal = db.get(Animal, body.animal_id)
    if animal is None or animal.fazenda_id != faz.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Matriz não encontrada nesta fazenda")
    ins = registrar_inseminacao(
        db, animal.id, faz.id, body.data or date.today(),
        body.touro, body.inseminador, body.protocolo,
    )
    db.commit()
    return _out(ins, animal.brinco)


@router.put("/inseminacoes/{ins_id}", response_model=InseminacaoOut)
def editar_inseminacao(
    ins_id: uuid.UUID,
    body: InseminacaoUpdateIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> InseminacaoOut:
    ins = _get_ins_no_escopo(ins_id, db, user)
    for campo, valor in body.model_dump(exclude_unset=True).items():
        setattr(ins, campo, valor)
    db.commit()
    brinco = db.get(Animal, ins.animal_id).brinco
    return _out(ins, brinco)


@router.put("/inseminacoes/{ins_id}/dg", response_model=InseminacaoOut)
def diagnostico(
    ins_id: uuid.UUID,
    body: DGIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> InseminacaoOut:
    if body.resultado not in ("prenhe", "vazia"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "resultado deve ser 'prenhe' ou 'vazia'")
    ins = _get_ins_no_escopo(ins_id, db, user)
    faz = get_fazenda_no_escopo(ins.fazenda_id, db, user)
    registrar_dg(db, ins, body.resultado, body.dg_data)
    db.commit()
    recomputar_taxa_prenhez(db, faz)  # DG muda a taxa de prenhez -> gatilho
    brinco = db.get(Animal, ins.animal_id).brinco
    return _out(ins, brinco)


@router.delete("/inseminacoes/{ins_id}", status_code=204)
def excluir_inseminacao(
    ins_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    ins = _get_ins_no_escopo(ins_id, db, user)
    faz = get_fazenda_no_escopo(ins.fazenda_id, db, user)
    db.delete(ins)
    db.commit()
    recomputar_taxa_prenhez(db, faz)
