import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Categorias pedidas pelo cliente (audio 10/11)
CATEGORIAS_INVENTARIO = ("maquina", "equipamento", "medicacao", "insumo", "outro")


class ItemInventario(Base):
    """Patrimonio/bem da fazenda: maquina (vagao, moinho, trator), equipamento
    (computador, barra de choque), medicacao, insumo. Sempre com localizacao —
    o cliente precisa saber ONDE cada coisa esta.
    """

    __tablename__ = "item_inventario"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    categoria: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    identificacao: Mapped[str | None] = mapped_column(String(80))  # n. serie / patrimonio / placa
    localizacao: Mapped[str | None] = mapped_column(String(120))   # onde esta hoje
    quantidade: Mapped[float | None] = mapped_column(Numeric(12, 3))
    unidade: Mapped[str | None] = mapped_column(String(20))        # un, kg, L, sc
    valor: Mapped[float | None] = mapped_column(Numeric(12, 2))
    situacao: Mapped[str] = mapped_column(String(20), default="ativo", nullable=False)  # ativo|manutencao|baixado
    data_aquisicao: Mapped[date | None] = mapped_column(Date)
    observacao: Mapped[str | None] = mapped_column(String(255))


class MovimentoInventario(Base):
    """Movimentacao do item entre locais/fazendas. Registra SEMPRE quem fez
    (audio 12: "ficar quem movimentou, quem deu entrada e quem deu saida").
    """

    __tablename__ = "movimento_inventario"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("item_inventario.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # entrada|saida|transferencia
    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantidade: Mapped[float | None] = mapped_column(Numeric(12, 3))
    origem: Mapped[str | None] = mapped_column(String(120))
    destino: Mapped[str | None] = mapped_column(String(120))
    # fazenda de destino quando e transferencia entre fazendas (audio 10)
    fazenda_destino_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("fazenda.id", ondelete="SET NULL")
    )
    # rastreabilidade — quem fez
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL")
    )
    usuario_nome: Mapped[str | None] = mapped_column(String(160))  # desnormalizado, sobrevive a exclusao
    observacao: Mapped[str | None] = mapped_column(String(255))
    # created_at/updated_at vem do Base
