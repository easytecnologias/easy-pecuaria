"""Inventario/patrimonio da fazenda (audio 10 e 11 do cliente).

Guarda maquinas, equipamentos, medicacoes e insumos SEMPRE com localizacao, e
registra a movimentacao entre locais/fazendas gravando QUEM movimentou.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventario import ItemInventario, MovimentoInventario
from app.models.organizacao import Fazenda


def listar_itens(db: Session, fazenda: Fazenda, categoria: str | None = None) -> list[ItemInventario]:
    stmt = select(ItemInventario).where(ItemInventario.fazenda_id == fazenda.id)
    if categoria:
        stmt = stmt.where(ItemInventario.categoria == categoria)
    return list(db.execute(stmt.order_by(ItemInventario.categoria, ItemInventario.nome)).scalars())


def resumo_inventario(db: Session, fazenda: Fazenda) -> dict:
    itens = listar_itens(db, fazenda)
    por_categoria: dict[str, int] = {}
    valor_total = 0.0
    for it in itens:
        por_categoria[it.categoria] = por_categoria.get(it.categoria, 0) + 1
        if it.valor:
            valor_total += float(it.valor)
    return {
        "total_itens": len(itens),
        "por_categoria": por_categoria,
        "valor_total": round(valor_total, 2),
        "itens": itens,
    }


def movimentar_item(
    db: Session, item: ItemInventario, tipo: str, data_ref: date,
    quantidade: float | None, origem: str | None, destino: str | None,
    fazenda_destino_id, obs: str | None, usuario=None,
) -> MovimentoInventario:
    """Registra a movimentacao e ja atualiza onde o item esta.

    Transferencia entre fazendas move o item de fazenda (o cliente pediu
    'do confinamento para a fazenda Perucaba e vice-versa').
    """
    m = MovimentoInventario(
        item_id=item.id, fazenda_id=item.fazenda_id, tipo=tipo, data=data_ref,
        quantidade=quantidade, origem=origem or item.localizacao, destino=destino,
        fazenda_destino_id=fazenda_destino_id, observacao=obs,
        usuario_id=getattr(usuario, "id", None),
        usuario_nome=getattr(usuario, "nome", None) or getattr(usuario, "email", None),
    )
    db.add(m)

    if destino:
        item.localizacao = destino
    if tipo == "transferencia" and fazenda_destino_id:
        item.fazenda_id = fazenda_destino_id
    # entrada/saida ajustam a quantidade em estoque (medicacao, insumo)
    if quantidade and item.quantidade is not None:
        atual = float(item.quantidade)
        item.quantidade = atual + quantidade if tipo == "entrada" else atual - quantidade

    db.commit()
    db.refresh(m)
    return m


def historico_item(db: Session, item: ItemInventario) -> list[MovimentoInventario]:
    return list(db.execute(
        select(MovimentoInventario)
        .where(MovimentoInventario.item_id == item.id)
        .order_by(MovimentoInventario.data.desc(), MovimentoInventario.created_at.desc())
    ).scalars())
