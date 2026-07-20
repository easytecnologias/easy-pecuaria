import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.inventario import CATEGORIAS_INVENTARIO, ItemInventario
from app.models.usuario import Usuario
from app.schemas import (
    ItemInventarioIn,
    ItemInventarioOut,
    MovimentoInventarioIn,
    MovimentoInventarioOut,
    ResumoInventario,
)
from app.services.inventario import (
    historico_item,
    listar_itens,
    movimentar_item,
    resumo_inventario,
)

router = APIRouter(tags=["inventario"])

TIPOS_MOV = ("entrada", "saida", "transferencia")


@router.get("/fazendas/{fazenda_id}/inventario", response_model=ResumoInventario)
def resumo(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ResumoInventario:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    r = resumo_inventario(db, faz)
    return ResumoInventario(
        total_itens=r["total_itens"], por_categoria=r["por_categoria"],
        valor_total=r["valor_total"],
        itens=[ItemInventarioOut.model_validate(i) for i in r["itens"]],
    )


@router.post("/fazendas/{fazenda_id}/inventario", response_model=ItemInventarioOut, status_code=201)
def novo_item(
    fazenda_id: uuid.UUID,
    body: ItemInventarioIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ItemInventario:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    if body.categoria not in CATEGORIAS_INVENTARIO:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"categoria invalida (use: {', '.join(CATEGORIAS_INVENTARIO)})",
        )
    item = ItemInventario(fazenda_id=faz.id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _item_no_escopo(item_id: uuid.UUID, db: Session, user: Usuario) -> ItemInventario:
    item = db.get(ItemInventario, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item nao encontrado")
    get_fazenda_no_escopo(item.fazenda_id, db, user)  # valida escopo por org/fazenda
    return item


@router.put("/inventario/{item_id}", response_model=ItemInventarioOut)
def editar_item(
    item_id: uuid.UUID,
    body: ItemInventarioIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ItemInventario:
    item = _item_no_escopo(item_id, db, user)
    for campo, valor in body.model_dump().items():
        setattr(item, campo, valor)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/inventario/{item_id}", status_code=204)
def excluir_item(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    item = _item_no_escopo(item_id, db, user)
    db.delete(item)
    db.commit()


@router.get("/inventario/{item_id}/movimentos", response_model=list[MovimentoInventarioOut])
def movimentos_do_item(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> list:
    item = _item_no_escopo(item_id, db, user)
    return historico_item(db, item)


@router.post("/inventario/{item_id}/movimentos", response_model=MovimentoInventarioOut, status_code=201)
def novo_movimento(
    item_id: uuid.UUID,
    body: MovimentoInventarioIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    item = _item_no_escopo(item_id, db, user)
    if body.tipo not in TIPOS_MOV:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"tipo invalido (use: {', '.join(TIPOS_MOV)})"
        )
    if body.tipo == "transferencia":
        if not body.fazenda_destino_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "informe a fazenda de destino")
        # destino tambem precisa estar no escopo do usuario
        get_fazenda_no_escopo(body.fazenda_destino_id, db, user)
    return movimentar_item(
        db, item, body.tipo, body.data or date.today(), body.quantidade,
        body.origem, body.destino, body.fazenda_destino_id, body.observacao, usuario=user,
    )
