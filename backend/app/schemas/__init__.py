import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import FormatoIndicador, Severidade


# --- Auth -------------------------------------------------------------------
class LoginIn(BaseModel):
    email: str
    senha: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    email: str
    papel: str
    is_superadmin: bool = False


# --- Fazenda ----------------------------------------------------------------
class FazendaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    municipio: str | None
    uf: str | None
    ativo: bool


class FazendaIn(BaseModel):
    nome: str
    municipio: str | None = None
    uf: str | None = None


class FazendaUpdateIn(BaseModel):
    nome: str | None = None
    municipio: str | None = None
    uf: str | None = None


# --- Painel / Dashboard -----------------------------------------------------
class IndicadorPainelOut(BaseModel):
    codigo: str
    nome: str
    categoria: str | None
    unidade: str | None
    formato: FormatoIndicador
    casas_decimais: int
    valor: float | None
    data_ref: date | None
    situacao: Severidade
    referencia: float | None
    acao: str | None


class FazendaPainelOut(BaseModel):
    id: uuid.UUID
    nome: str
    municipio: str | None
    uf: str | None
    alertas_abertos: int
    por_severidade: dict[str, int]
    indicadores: list[IndicadorPainelOut]


class ResumoDashboard(BaseModel):
    fazendas: int
    alertas_abertos: int
    por_severidade: dict[str, int]


class DashboardOut(BaseModel):
    organizacao: str
    resumo: ResumoDashboard
    fazendas: list[FazendaPainelOut]


# --- Alertas ----------------------------------------------------------------
class AlertaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    fazenda_id: uuid.UUID
    indicador_id: uuid.UUID
    severidade: Severidade
    status: str
    valor_observado: float | None
    valor_referencia: float | None
    mensagem: str
    acao: str | None
    avaliado_em: datetime
    resolvido_em: datetime | None


# --- Indicadores / lancamento de valores ------------------------------------
class IndicadorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    codigo: str
    nome: str
    categoria: str | None
    unidade: str | None
    formato: FormatoIndicador
    casas_decimais: int


class ValorIn(BaseModel):
    indicador_codigo: str
    valor: float
    data_ref: date | None = None
    observacao: str | None = None


class ParametroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    grupo: str | None
    chave: str
    rotulo: str
    valor: float
    unidade: str | None


class ParametroUpdateIn(BaseModel):
    valor: float


class RegraOut(BaseModel):
    id: uuid.UUID
    nome: str
    indicador_codigo: str
    indicador_nome: str
    operador: str
    tipo_referencia: str
    parametro_chave: str | None
    valor_referencia: float | None
    tolerancia: float | None
    severidade: Severidade
    acao: str


# --- Rebanho ----------------------------------------------------------------
class LoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    categoria: str | None
    local: str | None
    ativo: bool
    n_animais: int = 0
    # metas por lote (None = usa o padrao da fazenda)
    capacidade: int | None = None
    dias_cocho: int | None = None
    gmd_meta: float | None = None
    rendimento_carcaca: float | None = None


class LoteIn(BaseModel):
    nome: str
    categoria: str | None = None
    local: str | None = None
    capacidade: int | None = None
    dias_cocho: int | None = None
    gmd_meta: float | None = None
    rendimento_carcaca: float | None = None


class AnimalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    fazenda_id: uuid.UUID
    lote_id: uuid.UUID | None
    brinco: str
    categoria: str | None
    raca: str | None
    sexo: str | None
    data_nascimento: date | None
    mae_brinco: str | None
    pai: str | None
    origem: str | None
    status: str
    tipo_matriz: str | None = None
    desmama_data: date | None = None
    desmama_peso: float | None = None


class AnimalIn(BaseModel):
    brinco: str
    lote_id: uuid.UUID | None = None
    categoria: str | None = None
    raca: str | None = None
    sexo: str | None = None
    data_nascimento: date | None = None
    mae_brinco: str | None = None
    pai: str | None = None
    origem: str | None = None
    tipo_matriz: str | None = None
    desmama_data: date | None = None
    desmama_peso: float | None = None


class AnimalUpdateIn(BaseModel):
    brinco: str | None = None
    lote_id: uuid.UUID | None = None
    categoria: str | None = None
    raca: str | None = None
    sexo: str | None = None
    data_nascimento: date | None = None
    mae_brinco: str | None = None
    pai: str | None = None
    status: str | None = None
    tipo_matriz: str | None = None
    desmama_data: date | None = None
    desmama_peso: float | None = None


class LoteUpdateIn(BaseModel):
    nome: str | None = None
    categoria: str | None = None
    local: str | None = None
    capacidade: int | None = None
    dias_cocho: int | None = None
    gmd_meta: float | None = None
    rendimento_carcaca: float | None = None


class PesagemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    data: date
    peso: float
    gmd: float | None
    observacao: str | None


class PesagemIn(BaseModel):
    peso: float
    data: date | None = None
    observacao: str | None = None


# --- Reprodução ------------------------------------------------------------
class InseminacaoOut(BaseModel):
    id: uuid.UUID
    animal_id: uuid.UUID
    animal_brinco: str
    data: date
    touro: str
    inseminador: str | None
    protocolo: str | None
    resultado: str  # pendente | prenhe | vazia
    dg_data: date | None


class InseminacaoIn(BaseModel):
    animal_id: uuid.UUID
    touro: str
    data: date | None = None
    inseminador: str | None = None
    protocolo: str | None = None


class InseminacaoUpdateIn(BaseModel):
    data: date | None = None
    touro: str | None = None
    inseminador: str | None = None
    protocolo: str | None = None


class DGIn(BaseModel):
    resultado: str  # prenhe | vazia
    dg_data: date | None = None


class GrupoReproducao(BaseModel):
    nome: str
    total: int
    prenhes: int
    vazias: int
    taxa: float | None


class ResumoReproducao(BaseModel):
    total: int
    prenhes: int
    vazias: int
    pendentes: int
    taxa_prenhez: float | None
    por_touro: list[GrupoReproducao]
    por_inseminador: list[GrupoReproducao]
    inseminacoes: list[InseminacaoOut]


class EventoSanitarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tipo: str
    produto: str
    data: date
    proxima_aplicacao: date | None
    dose: str | None
    observacao: str | None


class MovimentoFichaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tipo: str
    data: date
    valor: float | None
    motivo: str | None


class FichaAnimalOut(BaseModel):
    animal: AnimalOut
    peso_atual: float | None
    gmd_atual: float | None
    pesagens: list[PesagemOut]
    inseminacoes: list[InseminacaoOut] = []
    sanitarios: list[EventoSanitarioOut] = []
    movimentos: list[MovimentoFichaOut] = []


# --- Estoque de volumoso ----------------------------------------------------
class MovimentoIn(BaseModel):
    tipo: str  # entrada | saida
    quantidade_t: float
    data: date | None = None
    descricao: str | None = None


class MovimentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    data: date
    tipo: str
    quantidade_t: float
    descricao: str | None


class ResumoEstoque(BaseModel):
    saldo_t: float
    consumo_diario_t: float | None
    dias: float | None
    movimentos: list[MovimentoOut]


# --- Nutrição / dieta -------------------------------------------------------
class ItemDietaIn(BaseModel):
    ingrediente: str
    inclusao_kg: float
    preco_kg: float
    ms_pct: float  # 0..1


class ItemDietaOut(ItemDietaIn):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class DietaIn(BaseModel):
    nome: str
    lote_id: uuid.UUID | None = None
    itens: list[ItemDietaIn]


class DietaOut(BaseModel):
    id: uuid.UUID
    nome: str
    lote_id: uuid.UUID | None
    lote_nome: str | None
    data: date
    ativa: bool
    itens: list[ItemDietaOut]
    custo_cab_dia: float
    consumo_ms_pv: float | None
    kg_ms: float
    peso_medio_lote: float | None


# --- Mercado & custos -------------------------------------------------------
class CotacaoArrobaIn(BaseModel):
    valor: float
    data: date | None = None


class CotacaoArrobaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    data: date
    valor: float
    origem: str
    fonte: str | None


class CotacaoInsumoIn(BaseModel):
    insumo: str
    preco_origem: float
    ms_pct: float
    data: date | None = None
    praca: str | None = None
    unidade: str = "kg"
    frete: float = 0
    outros: float = 0


class CotacaoInsumoOut(BaseModel):
    id: uuid.UUID
    data: date
    insumo: str
    praca: str | None
    unidade: str
    preco_origem: float
    frete: float
    outros: float
    ms_pct: float
    custo_entregue_kg: float
    custo_kg_ms: float | None


class ResumoMercado(BaseModel):
    arroba_atual: float | None
    arroba_data: date | None
    historico: list[CotacaoArrobaOut]
    insumos: list[CotacaoInsumoOut]


class BuscaArroba(BaseModel):
    encontrado: bool
    valor: float | None = None
    fonte: str | None = None


# --- Sanitário --------------------------------------------------------------
class AplicacaoIn(BaseModel):
    tipo: str  # vacina|vermifugo|tratamento|exame|carrapaticida|hormonio
    produto: str
    data: date | None = None
    proxima_aplicacao: date | None = None
    dose: str | None = None
    observacao: str | None = None
    animal_id: uuid.UUID | None = None   # aplica num animal
    lote_id: uuid.UUID | None = None      # ou no lote inteiro


class AgendaSanitariaItem(BaseModel):
    produto: str
    tipo: str
    proxima: date
    animais: int
    vencido: bool
    vence_proximo: bool


class HistoricoSanitarioItem(BaseModel):
    id: uuid.UUID
    brinco: str
    tipo: str
    produto: str
    data: date
    proxima: date | None
    dose: str | None


class ResumoSanitario(BaseModel):
    total: int
    vencendo: int
    agenda: list[AgendaSanitariaItem]
    historico: list[HistoricoSanitarioItem]


# --- Movimentação de animais ------------------------------------------------
class MovimentoAnimalIn(BaseModel):
    tipo: str  # compra|venda|morte|descarte|transferencia
    data: date | None = None
    valor: float | None = None
    motivo: str | None = None
    lote_destino_id: uuid.UUID | None = None
    observacao: str | None = None


class MovimentoAnimalItem(BaseModel):
    id: uuid.UUID
    brinco: str
    tipo: str
    data: date
    valor: float | None
    motivo: str | None
    usuario_nome: str | None = None  # quem movimentou (audio 12)


class ResumoMovimentos(BaseModel):
    vendas_30d: int
    mortes_30d: int
    descartes_30d: int
    compras_30d: int
    movimentos: list[MovimentoAnimalItem]


class CategoriaComposicao(BaseModel):
    categoria: str
    total: int


class ComposicaoRebanho(BaseModel):
    total: int
    femeas: int
    machos: int
    por_categoria: list[CategoriaComposicao]


class LancamentoIn(BaseModel):
    tipo: str  # despesa | receita
    categoria: str
    valor: float
    data: date | None = None
    descricao: str | None = None


class LancamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    data: date
    tipo: str
    categoria: str
    valor: float
    descricao: str | None


class CategoriaFinanceira(BaseModel):
    tipo: str
    categoria: str
    total: float


class ResumoFinanceiro(BaseModel):
    receitas: float
    despesas: float
    saldo: float
    n_animais: int
    margem_cab: float | None
    capital_giro_dias: int | None
    categorias: list[CategoriaFinanceira]
    lancamentos: list[LancamentoOut]


class MesEvolucao(BaseModel):
    periodo: str
    label: str
    ano: str
    nascimentos: int


class EvolucaoRebanhoOut(BaseModel):
    meses: list[MesEvolucao]
    total_nascimentos_12m: int
    total_ativos: int


class PartoIn(BaseModel):
    mae_id: uuid.UUID
    data: date | None = None
    resultado: str = "nascido_vivo"  # nascido_vivo | natimorto
    sexo_bezerro: str | None = None  # M | F
    brinco_bezerro: str | None = None
    peso_nascimento: float | None = None
    observacao: str | None = None


class PartoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    data: date
    mae_id: uuid.UUID
    mae_brinco: str
    bezerro_id: uuid.UUID | None
    resultado: str
    sexo_bezerro: str | None
    brinco_bezerro: str | None
    peso_nascimento: float | None
    observacao: str | None


class ResumoPartos(BaseModel):
    partos_12m: int
    vivos_12m: int
    natimortos_12m: int
    taxa_natimortalidade: float | None
    matrizes: int
    taxa_natalidade: float | None
    partos: list[PartoOut]


class EscoreIn(BaseModel):
    animal_id: uuid.UUID
    escore: float
    data: date | None = None
    observacao: str | None = None


class EscoreHistItem(BaseModel):
    id: uuid.UUID
    animal_id: uuid.UUID
    brinco: str
    categoria: str | None
    data: date
    escore: float
    observacao: str | None


class ResumoEscore(BaseModel):
    n_avaliados: int
    media: float | None
    magras: int
    ideais: int
    gordas: int
    pct_ideais: float | None
    historico: list[EscoreHistItem]


class UsuarioAdminOut(BaseModel):
    id: uuid.UUID
    nome: str
    email: str
    papel: str
    ativo: bool
    fazenda_ids: list[uuid.UUID]


class UsuarioCreateIn(BaseModel):
    nome: str
    email: str
    senha: str
    papel: str = "gerente"
    fazenda_ids: list[uuid.UUID] = []


class UsuarioUpdateIn(BaseModel):
    nome: str | None = None
    papel: str | None = None
    ativo: bool | None = None
    fazenda_ids: list[uuid.UUID] | None = None


class SenhaResetIn(BaseModel):
    senha: str


class OrganizacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    slug: str


class OrganizacaoUpdateIn(BaseModel):
    nome: str


class OrgPlataformaOut(BaseModel):
    id: uuid.UUID
    nome: str
    slug: str
    n_fazendas: int
    n_usuarios: int


class OrgCreateIn(BaseModel):
    nome: str
    slug: str
    admin_nome: str
    admin_email: str
    admin_senha: str


class OrgRenomearIn(BaseModel):
    nome: str


class AuditLogOut(BaseModel):
    id: uuid.UUID
    usuario_email: str
    acao: str
    entidade: str | None
    entidade_id: uuid.UUID | None
    detalhe: str | None
    created_at: datetime


class TrocarSenhaIn(BaseModel):
    senha_atual: str
    senha_nova: str


class PesagemRelItem(BaseModel):
    brinco: str
    categoria: str | None
    lote: str | None
    peso: float
    data: date
    gmd: float | None


class RelatorioPesagem(BaseModel):
    total: int
    com_pesagem: int
    peso_medio: float | None
    gmd_medio: float | None
    arroba_media: float | None
    animais: list[PesagemRelItem]


# --- Inventario / patrimonio (audio 10 e 11) --------------------------------
class ItemInventarioIn(BaseModel):
    categoria: str
    nome: str
    identificacao: str | None = None
    localizacao: str | None = None
    quantidade: float | None = None
    unidade: str | None = None
    valor: float | None = None
    situacao: str = "ativo"
    data_aquisicao: date | None = None
    observacao: str | None = None


class ItemInventarioOut(ItemInventarioIn):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    fazenda_id: uuid.UUID


class MovimentoInventarioIn(BaseModel):
    tipo: str  # entrada | saida | transferencia
    data: date | None = None
    quantidade: float | None = None
    origem: str | None = None
    destino: str | None = None
    fazenda_destino_id: uuid.UUID | None = None
    observacao: str | None = None


class MovimentoInventarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    item_id: uuid.UUID
    tipo: str
    data: date
    quantidade: float | None
    origem: str | None
    destino: str | None
    fazenda_destino_id: uuid.UUID | None
    usuario_nome: str | None   # quem movimentou (audio 12)
    observacao: str | None


class ResumoInventario(BaseModel):
    total_itens: int
    por_categoria: dict[str, int]
    valor_total: float
    itens: list[ItemInventarioOut]


# --- Desmame (audio 7) ------------------------------------------------------
class DesmamaIn(BaseModel):
    data: date | None = None
    peso: float


class ResumoDesmama(BaseModel):
    matrizes: int
    bezerros: int
    desmamados: int
    taxa_desmama: float | None
    taxa_desmama_meta: float | None
    peso_medio_desmama: float | None
    peso_desmama_meta: float | None
    por_tipo_matriz: dict[str, int]
