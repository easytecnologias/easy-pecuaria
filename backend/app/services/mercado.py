"""Mercado & custos: cotação de arroba -> indicador arroba_recebida; cotação de
insumos -> custo por kg de MS. Busca de arroba é best-effort (fonte externa
instável); a base confiável é a entrada manual.
"""

from __future__ import annotations

import re
import urllib.request
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mercado import CotacaoArroba, CotacaoInsumo
from app.models.organizacao import Fazenda
from app.services.gatilhos import sincronizar_alertas
from app.services.indicador_util import upsert_indicador


def registrar_cotacao_arroba(
    db: Session, fazenda: Fazenda, data_ref: date, valor: float,
    origem: str = "manual", fonte: str | None = None,
) -> CotacaoArroba:
    cot = CotacaoArroba(
        fazenda_id=fazenda.id, data=data_ref, valor=valor, origem=origem, fonte=fonte
    )
    db.add(cot)
    db.commit()
    upsert_indicador(db, fazenda.id, "arroba_recebida", valor, data_ref)
    db.commit()
    sincronizar_alertas(db, fazenda)
    return cot


def custo_kg_ms(cot: CotacaoInsumo) -> tuple[float, float | None]:
    """Retorna (custo_entregue_por_kg_MN, custo_por_kg_MS)."""
    entregue = float(cot.preco_origem) + float(cot.frete) + float(cot.outros)
    por_kg = entregue / 1000 if cot.unidade == "t" else entregue
    ms = float(cot.ms_pct)
    kg_ms = round(por_kg / ms, 4) if ms > 0 else None
    return round(por_kg, 4), kg_ms


def resumo_mercado(db: Session, fazenda: Fazenda) -> dict:
    arrobas = db.execute(
        select(CotacaoArroba).where(CotacaoArroba.fazenda_id == fazenda.id)
        .order_by(CotacaoArroba.data.desc()).limit(30)
    ).scalars().all()
    insumos = db.execute(
        select(CotacaoInsumo).where(CotacaoInsumo.fazenda_id == fazenda.id)
        .order_by(CotacaoInsumo.data.desc())
    ).scalars().all()
    return {
        "arroba_atual": float(arrobas[0].valor) if arrobas else None,
        "arroba_data": arrobas[0].data if arrobas else None,
        "historico": arrobas,
        "insumos": insumos,
    }


def buscar_cotacao_arroba() -> tuple[float, str] | None:
    """Best-effort: tenta ler a arroba do boi gordo de uma fonte pública alcançável.
    Retorna (valor, fonte) ou None. NUNCA lança — é só um atalho; o manual é a base.
    """
    url = "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            html = r.read().decode("utf-8", errors="ignore")
        # procura o primeiro valor no formato de arroba (ex: 315,00 / 312,50)
        m = re.search(r"([12]\d{2},\d{2})", html)
        if m:
            valor = float(m.group(1).replace(".", "").replace(",", "."))
            if 150 <= valor <= 600:  # sanidade: faixa plausível da @
                return valor, "Notícias Agrícolas (best-effort)"
    except Exception:
        return None
    return None
