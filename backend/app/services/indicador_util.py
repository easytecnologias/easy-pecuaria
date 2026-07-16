from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.indicador import IndicadorDefinicao, IndicadorValor


def upsert_indicador(db: Session, fazenda_id, codigo: str, valor: float, quando: date | None = None) -> None:
    """Grava/atualiza o valor de um indicador para a fazenda na data (default hoje)."""
    quando = quando or date.today()
    ind = db.execute(
        select(IndicadorDefinicao).where(IndicadorDefinicao.codigo == codigo)
    ).scalar_one_or_none()
    if ind is None:
        return
    existente = db.execute(
        select(IndicadorValor).where(
            IndicadorValor.fazenda_id == fazenda_id,
            IndicadorValor.indicador_id == ind.id,
            IndicadorValor.data_ref == quando,
        )
    ).scalar_one_or_none()
    if existente:
        existente.valor = valor
    else:
        db.add(IndicadorValor(
            fazenda_id=fazenda_id, indicador_id=ind.id,
            valor=valor, data_ref=quando, origem="calculo",
        ))
