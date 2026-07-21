"""Modelos SQLAlchemy. Importados aqui para o Alembic detectar todas as tabelas."""

from app.core.db import Base
from app.models.auditoria import AuditLog
from app.models.gatilho import Alerta, RegraGatilho
from app.models.indicador import IndicadorDefinicao, IndicadorValor
from app.models.organizacao import Fazenda, Organizacao
from app.models.parametro import Parametro
from app.models.planejamento import Atividade
from app.models.silagem import Silagem
from app.models.escore import EscoreCorporal
from app.models.estoque import MovimentoVolumoso
from app.models.financeiro import ContaFinanceira, LancamentoFinanceiro
from app.models.inventario import ItemInventario, MovimentoInventario
from app.models.mercado import CotacaoArroba, CotacaoInsumo
from app.models.movimento import MovimentoAnimal
from app.models.nutricao import Dieta, ItemDieta
from app.models.parto import Parto
from app.models.sanitario import EventoSanitario
from app.models.rebanho import Animal, Lote, Pesagem
from app.models.reproducao import Inseminacao
from app.models.usuario import Usuario, UsuarioFazenda

__all__ = [
    "Base",
    "Organizacao",
    "Fazenda",
    "Usuario",
    "UsuarioFazenda",
    "Parametro",
    "IndicadorDefinicao",
    "IndicadorValor",
    "RegraGatilho",
    "Alerta",
    "AuditLog",
    "Lote",
    "Animal",
    "Pesagem",
    "Inseminacao",
    "Parto",
    "MovimentoVolumoso",
    "LancamentoFinanceiro",
    "EscoreCorporal",
    "Dieta",
    "ItemDieta",
    "CotacaoArroba",
    "CotacaoInsumo",
    "EventoSanitario",
    "MovimentoAnimal",
    "ItemInventario",
    "MovimentoInventario",
    "Atividade",
    "Silagem",
    "ContaFinanceira",
]
