"""Criacao de fazenda ja com as metas/premissas padrao — senao os gatilhos que
dependem de parametros (custo_max_dieta, gmd_meta, etc.) nao teriam limite.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.organizacao import Fazenda
from app.models.parametro import Parametro
from app.models.usuario import UsuarioFazenda

# (grupo, chave, rotulo, valor, unidade) — mesmas premissas do plano diretor
PREMISSAS_PADRAO = [
    ("Rebanho", "matrizes_iniciais", "Matrizes iniciais", 300, "cabecas"),
    ("Rebanho", "taxa_prenhez_meta", "Taxa de prenhez meta", 0.82, "%"),
    ("Rebanho", "taxa_desmama_meta", "Taxa de desmama meta", 0.76, "%"),
    ("Rebanho", "peso_desmama", "Peso medio desmama", 220, "kg"),
    ("Confinamento", "capacidade_confinamento", "Capacidade inicial", 300, "cab/ciclo"),
    ("Confinamento", "quantidade_lotes", "Quantidade de lotes", 4, "lotes"),
    ("Confinamento", "espaco_por_lote", "Espaco por lote", 75, "cab/lote"),
    ("Confinamento", "ciclos_ano", "Ciclos por ano", 2, "ciclos"),
    # Padroes da fazenda; cada lote pode sobrescrever (ver Lote.dias_cocho/gmd_meta/rendimento_carcaca)
    ("Confinamento", "dias_cocho", "Dias de cocho (padrao)", 105, "dias"),
    ("Confinamento", "gmd_meta", "GMD meta (padrao)", 1.55, "kg/dia"),
    ("Confinamento", "rendimento_carcaca", "Rendimento de carcaca (padrao)", 0.55, "%"),
    ("Mercado", "arroba_base", "Arroba projetada base", 310, "R$/@"),
    ("Mercado", "arroba_ruim", "Arroba cenario ruim", 265, "R$/@"),
    ("Mercado", "arroba_favoravel", "Arroba cenario favoravel", 350, "R$/@"),
    ("Dieta", "consumo_ms_pv", "Consumo MS (% PV)", 0.024, "%PV/dia"),
    ("Dieta", "custo_max_dieta", "Custo maximo dieta", 13.5, "R$/cab/dia"),
    ("Silagem", "ms_alvo_ensilagem", "MS alvo na ensilagem", 0.34, "%"),
    ("Silagem", "perda_silo", "Perda total de silo", 0.12, "%"),
    ("Silagem", "estoque_seguranca", "Estoque de seguranca", 45, "dias"),
    ("Financeiro", "capital_giro_min", "Capital de giro minimo", 90, "dias"),
]


def criar_fazenda(
    db: Session, org_id, usuario_id, nome: str, municipio: str | None, uf: str | None
) -> Fazenda:
    faz = Fazenda(org_id=org_id, nome=nome, municipio=municipio, uf=uf)
    db.add(faz)
    db.flush()
    for grupo, chave, rotulo, valor, unidade in PREMISSAS_PADRAO:
        db.add(Parametro(
            fazenda_id=faz.id, grupo=grupo, chave=chave,
            rotulo=rotulo, valor=valor, unidade=unidade,
        ))
    # vincula o criador (admin/direcao ja veem todas, mas garante acesso)
    if not db.get(UsuarioFazenda, {"usuario_id": usuario_id, "fazenda_id": faz.id}):
        db.add(UsuarioFazenda(usuario_id=usuario_id, fazenda_id=faz.id))
    db.commit()
    db.refresh(faz)
    return faz
