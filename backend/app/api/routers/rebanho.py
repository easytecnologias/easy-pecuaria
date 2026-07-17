import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.rebanho import Animal, Lote, Pesagem
from app.models.reproducao import Inseminacao
from app.models.usuario import Usuario
from app.schemas import (
    AnimalIn,
    AnimalOut,
    AnimalUpdateIn,
    FichaAnimalOut,
    InseminacaoOut,
    LoteIn,
    LoteOut,
    PesagemRelItem,
    RelatorioPesagem,
    LoteUpdateIn,
    PesagemIn,
    PesagemOut,
)
from app.services.rebanho import recomputar_indicadores_rebanho, registrar_pesagem

router = APIRouter(tags=["rebanho"])


def _get_animal_no_escopo(animal_id: uuid.UUID, db: Session, user: Usuario) -> Animal:
    animal = db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal nao encontrado")
    get_fazenda_no_escopo(animal.fazenda_id, db, user)  # valida acesso
    return animal


# ---- Lotes ----
@router.get("/fazendas/{fazenda_id}/lotes", response_model=list[LoteOut])
def listar_lotes(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> list[LoteOut]:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    contagem = dict(
        db.execute(
            select(Animal.lote_id, func.count(Animal.id))
            .where(Animal.fazenda_id == faz.id, Animal.status == "ativo")
            .group_by(Animal.lote_id)
        ).all()
    )
    lotes = db.execute(
        select(Lote).where(Lote.fazenda_id == faz.id, Lote.ativo.is_(True)).order_by(Lote.nome)
    ).scalars().all()
    return [
        LoteOut(
            id=l.id, nome=l.nome, categoria=l.categoria, local=l.local,
            ativo=l.ativo, n_animais=contagem.get(l.id, 0),
        )
        for l in lotes
    ]


@router.post("/fazendas/{fazenda_id}/lotes", response_model=LoteOut, status_code=201)
def criar_lote(
    fazenda_id: uuid.UUID,
    body: LoteIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> LoteOut:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    lote = Lote(fazenda_id=faz.id, nome=body.nome, categoria=body.categoria, local=body.local)
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return LoteOut(id=lote.id, nome=lote.nome, categoria=lote.categoria,
                   local=lote.local, ativo=lote.ativo, n_animais=0)


def _get_lote_no_escopo(fazenda_id, lote_id, db, user) -> Lote:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    lote = db.get(Lote, lote_id)
    if lote is None or lote.fazenda_id != faz.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lote nao encontrado")
    return lote


@router.put("/fazendas/{fazenda_id}/lotes/{lote_id}", response_model=LoteOut)
def atualizar_lote(
    fazenda_id: uuid.UUID,
    lote_id: uuid.UUID,
    body: LoteUpdateIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> LoteOut:
    lote = _get_lote_no_escopo(fazenda_id, lote_id, db, user)
    for campo, valor in body.model_dump(exclude_unset=True).items():
        setattr(lote, campo, valor)
    db.commit()
    db.refresh(lote)
    n = db.execute(
        select(func.count(Animal.id)).where(Animal.lote_id == lote.id, Animal.status == "ativo")
    ).scalar_one()
    return LoteOut(id=lote.id, nome=lote.nome, categoria=lote.categoria,
                   local=lote.local, ativo=lote.ativo, n_animais=n)


@router.delete("/fazendas/{fazenda_id}/lotes/{lote_id}", status_code=204)
def excluir_lote(
    fazenda_id: uuid.UUID,
    lote_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    lote = _get_lote_no_escopo(fazenda_id, lote_id, db, user)
    n = db.execute(
        select(func.count(Animal.id)).where(Animal.lote_id == lote.id)
    ).scalar_one()
    if n > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"O lote tem {n} animal(is). Mova ou exclua os animais antes de apagar o lote.",
        )
    db.delete(lote)
    db.commit()


# ---- Animais ----
@router.get("/fazendas/{fazenda_id}/animais", response_model=list[AnimalOut])
def listar_animais(
    fazenda_id: uuid.UUID,
    lote_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> list[Animal]:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    stmt = select(Animal).where(Animal.fazenda_id == faz.id)
    if lote_id is not None:
        stmt = stmt.where(Animal.lote_id == lote_id)
    return list(db.execute(stmt.order_by(Animal.brinco)).scalars().all())


@router.post("/fazendas/{fazenda_id}/animais", response_model=AnimalOut, status_code=201)
def criar_animal(
    fazenda_id: uuid.UUID,
    body: AnimalIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Animal:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    ja = db.execute(
        select(Animal).where(Animal.fazenda_id == faz.id, Animal.brinco == body.brinco)
    ).scalar_one_or_none()
    if ja:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ja existe animal com esse brinco")
    animal = Animal(fazenda_id=faz.id, **body.model_dump())
    db.add(animal)
    db.commit()
    db.refresh(animal)
    # novo animal muda a ocupacao do confinamento
    recomputar_indicadores_rebanho(db, faz)
    return animal


@router.put("/animais/{animal_id}", response_model=AnimalOut)
def atualizar_animal(
    animal_id: uuid.UUID,
    body: AnimalUpdateIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Animal:
    animal = _get_animal_no_escopo(animal_id, db, user)
    dados = body.model_dump(exclude_unset=True)
    novo_brinco = dados.get("brinco")
    if novo_brinco and novo_brinco != animal.brinco:
        existe = db.execute(
            select(Animal).where(
                Animal.fazenda_id == animal.fazenda_id,
                Animal.brinco == novo_brinco,
                Animal.id != animal.id,
            )
        ).scalar_one_or_none()
        if existe:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ja existe animal com esse brinco")
    for campo, valor in dados.items():
        setattr(animal, campo, valor)
    db.commit()
    db.refresh(animal)
    faz = get_fazenda_no_escopo(animal.fazenda_id, db, user)
    recomputar_indicadores_rebanho(db, faz)  # mudanca de lote/status afeta ocupacao
    return animal


@router.delete("/animais/{animal_id}", status_code=204)
def excluir_animal(
    animal_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    animal = _get_animal_no_escopo(animal_id, db, user)
    faz_id = animal.fazenda_id
    db.delete(animal)
    db.commit()
    faz = get_fazenda_no_escopo(faz_id, db, user)
    recomputar_indicadores_rebanho(db, faz)


@router.get("/animais/{animal_id}", response_model=FichaAnimalOut)
def ficha_animal(
    animal_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> FichaAnimalOut:
    animal = _get_animal_no_escopo(animal_id, db, user)
    pesagens = db.execute(
        select(Pesagem).where(Pesagem.animal_id == animal.id).order_by(Pesagem.data.desc())
    ).scalars().all()
    peso_atual = float(pesagens[0].peso) if pesagens else None
    gmd_atual = next((float(p.gmd) for p in pesagens if p.gmd is not None), None)
    inseminacoes = db.execute(
        select(Inseminacao).where(Inseminacao.animal_id == animal.id).order_by(Inseminacao.data.desc())
    ).scalars().all()
    from app.schemas import EventoSanitarioOut, MovimentoFichaOut
    from app.services.movimento import movimentos_do_animal
    from app.services.sanitario import eventos_do_animal
    return FichaAnimalOut(
        animal=AnimalOut.model_validate(animal),
        peso_atual=peso_atual,
        gmd_atual=gmd_atual,
        pesagens=[PesagemOut.model_validate(p) for p in pesagens],
        inseminacoes=[
            InseminacaoOut(
                id=i.id, animal_id=i.animal_id, animal_brinco=animal.brinco, data=i.data,
                touro=i.touro, inseminador=i.inseminador, protocolo=i.protocolo,
                resultado=i.resultado, dg_data=i.dg_data,
            ) for i in inseminacoes
        ],
        sanitarios=[EventoSanitarioOut.model_validate(e) for e in eventos_do_animal(db, animal.id)],
        movimentos=[MovimentoFichaOut.model_validate(m) for m in movimentos_do_animal(db, animal.id)],
    )


@router.post("/animais/{animal_id}/pesagens", response_model=FichaAnimalOut, status_code=201)
def lancar_pesagem(
    animal_id: uuid.UUID,
    body: PesagemIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> FichaAnimalOut:
    animal = _get_animal_no_escopo(animal_id, db, user)
    faz = get_fazenda_no_escopo(animal.fazenda_id, db, user)
    registrar_pesagem(db, animal, body.data or date.today(), body.peso, body.observacao)
    db.commit()
    # evento -> indicador -> gatilho
    recomputar_indicadores_rebanho(db, faz)
    return ficha_animal(animal_id, db, user)


@router.get("/fazendas/{fazenda_id}/relatorio-pesagem", response_model=RelatorioPesagem)
def relatorio_pesagem(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> RelatorioPesagem:
    """Última pesagem de cada animal da fazenda + médias (peso, GMD, @)."""
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    ult = (
        select(Pesagem.animal_id, func.max(Pesagem.data).label("dmax"))
        .where(Pesagem.fazenda_id == faz.id)
        .group_by(Pesagem.animal_id)
        .subquery()
    )
    rows = db.execute(
        select(Animal.brinco, Animal.categoria, Lote.nome, Pesagem.peso, Pesagem.data, Pesagem.gmd)
        .join(Pesagem, Pesagem.animal_id == Animal.id)
        .join(ult, (Pesagem.animal_id == ult.c.animal_id) & (Pesagem.data == ult.c.dmax))
        .outerjoin(Lote, Lote.id == Animal.lote_id)
        .where(Animal.fazenda_id == faz.id)
        .order_by(Animal.brinco)
    ).all()

    itens = [
        PesagemRelItem(
            brinco=brinco, categoria=categoria, lote=lote,
            peso=float(peso), data=data, gmd=float(gmd) if gmd is not None else None,
        )
        for brinco, categoria, lote, peso, data, gmd in rows
    ]
    total = int(db.execute(
        select(func.count(Animal.id)).where(Animal.fazenda_id == faz.id, Animal.status == "ativo")
    ).scalar_one())
    pesos = [i.peso for i in itens]
    gmds = [i.gmd for i in itens if i.gmd is not None]
    peso_medio = round(sum(pesos) / len(pesos), 1) if pesos else None
    gmd_medio = round(sum(gmds) / len(gmds), 3) if gmds else None
    arroba_media = round(peso_medio / 30, 2) if peso_medio else None
    return RelatorioPesagem(
        total=total, com_pesagem=len(itens),
        peso_medio=peso_medio, gmd_medio=gmd_medio, arroba_media=arroba_media,
        animais=itens,
    )
