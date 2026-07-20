"""Seed inicial: organizacao + 3 fazendas + premissas + catalogo de indicadores +
regras de gatilho (todas extraidas do Plano Diretor Pecuario) + alguns valores de
exemplo para o painel ja mostrar situacao real.

Rodar:  python -m app.seed.seed
Idempotente: se a organizacao 'jln' ja existir, nao recria.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import hash_senha
from app.models.enums import (
    FormatoIndicador,
    Operador,
    OrigemValor,
    PapelUsuario,
    Severidade,
    TipoReferencia,
)
from app.models.gatilho import RegraGatilho
from app.models.indicador import IndicadorDefinicao, IndicadorValor
from app.models.organizacao import Fazenda, Organizacao
from app.models.parametro import Parametro
from app.models.usuario import Usuario, UsuarioFazenda

# --- Premissas (aba 'Premissas' da planilha) --------------------------------
# (grupo, chave, rotulo, valor, unidade)
PREMISSAS = [
    ("Rebanho", "matrizes_iniciais", "Matrizes iniciais", 300, "cabecas"),
    ("Rebanho", "taxa_prenhez_meta", "Taxa de prenhez meta", 0.82, "%"),
    ("Rebanho", "taxa_desmama_meta", "Taxa de desmama meta", 0.76, "%"),
    ("Rebanho", "peso_desmama", "Peso medio desmama", 220, "kg"),
    ("Confinamento", "capacidade_confinamento", "Capacidade inicial", 300, "cab/ciclo"),
    ("Confinamento", "quantidade_lotes", "Quantidade de lotes", 4, "lotes"),
    ("Confinamento", "espaco_por_lote", "Espaco por lote", 75, "cab/lote"),
    ("Confinamento", "ciclos_ano", "Ciclos por ano", 2, "ciclos"),
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
    ("Clima", "reducao_seca", "Reducao produtividade (seca)", 0.25, "%"),
    ("Financeiro", "capital_giro_min", "Capital de giro minimo", 90, "dias"),
]

# --- Catalogo de indicadores (KPIs do painel) -------------------------------
# (codigo, nome, categoria, unidade, formato, casas)
INDICADORES = [
    ("custo_dieta_cab_dia", "Custo da dieta", "Dieta", "R$/cab/dia", FormatoIndicador.moeda, 2),
    ("consumo_ms_pv", "Consumo de MS (% PV)", "Dieta", "%PV/dia", FormatoIndicador.percentual, 3),
    ("taxa_prenhez", "Taxa de prenhez", "Reproducao", "%", FormatoIndicador.percentual, 2),
    ("ocupacao_confinamento", "Ocupacao do confinamento", "Confinamento", "%", FormatoIndicador.percentual, 2),
    ("estoque_silagem_dias", "Estoque de silagem", "Volumoso", "dias", FormatoIndicador.dias, 0),
    ("gmd", "GMD do lote", "Confinamento", "kg/dia", FormatoIndicador.numero, 2),
    ("arroba_recebida", "Arroba recebida", "Mercado", "R$/@", FormatoIndicador.moeda, 2),
    ("margem_cab", "Margem por cabeca", "Financeiro", "R$", FormatoIndicador.moeda, 2),
    ("capital_giro_dias", "Capital de giro", "Financeiro", "dias", FormatoIndicador.dias, 0),
    ("peso_desmama_real", "Peso medio de desmama", "Reproducao", "kg", FormatoIndicador.numero, 1),
    ("taxa_desmama", "Taxa de desmama", "Reproducao", "%", FormatoIndicador.percentual, 2),
]

# --- Regras de gatilho (aba 'Dashboard' -> colunas Regra/Acao) --------------
# (indicador, nome, operador, tipo_ref, valor_fixo, parametro_chave, tolerancia, severidade, acao)
REGRAS = [
    ("custo_dieta_cab_dia", "Custo da dieta acima da meta", Operador.gt,
     TipoReferencia.parametro, None, "custo_max_dieta", None, Severidade.alerta,
     "Revisar ingredientes e preco entregue (frete, perdas, impostos)."),
    ("consumo_ms_pv", "Consumo de MS fora do alvo", Operador.abs_diff_gt,
     TipoReferencia.parametro, None, "consumo_ms_pv", 0.003, Severidade.revisar,
     "Validar peso vivo, teor de MS e inclusao dos ingredientes."),
    ("estoque_silagem_dias", "Estoque de silagem abaixo da seguranca", Operador.lt,
     TipoReferencia.parametro, None, "estoque_seguranca", None, Severidade.alerta,
     "Comprar/produzir volumoso e reduzir lotacao."),
    ("ocupacao_confinamento", "Ocupacao alta - avaliar expansao", Operador.gt,
     TipoReferencia.valor_fixo, 0.85, None, None, Severidade.avaliar,
     "Avaliar expansao somente com os 4 gatilhos: ocupacao >85%, margem/cab > meta, silagem >120 dias, caixa >90 dias."),
    ("taxa_prenhez", "Prenhez abaixo da meta", Operador.lt,
     TipoReferencia.parametro, None, "taxa_prenhez_meta", None, Severidade.revisar,
     "Investigar protocolo, ECC e execucao da IATF (por touro e inseminador)."),
    ("gmd", "GMD abaixo da meta", Operador.lt,
     TipoReferencia.parametro, None, "gmd_meta", None, Severidade.revisar,
     "Auditar trato, cocho, sanidade e pesagens do lote."),
    ("capital_giro_dias", "Capital de giro abaixo do minimo", Operador.lt,
     TipoReferencia.parametro, None, "capital_giro_min", None, Severidade.alerta,
     "Reforcar caixa antes de qualquer expansao."),
    ("peso_desmama_real", "Peso de desmama abaixo da meta", Operador.lt,
     TipoReferencia.parametro, None, "peso_desmama", None, Severidade.revisar,
     "Revisar suplementacao de cria, sanidade do bezerro e ECC da matriz."),
    ("taxa_desmama", "Taxa de desmama abaixo da meta", Operador.lt,
     TipoReferencia.parametro, None, "taxa_desmama_meta", None, Severidade.alerta,
     "Investigar perda de bezerro entre nascimento e desmama."),
]

# --- Valores de exemplo para a Fazenda Sede (mix de OK/alerta) --------------
# (indicador, valor)
VALORES_EXEMPLO_SEDE = [
    ("custo_dieta_cab_dia", 14.20),   # > 13.5  -> ALERTA
    ("consumo_ms_pv", 0.024),         # == meta -> OK
    ("estoque_silagem_dias", 38),     # < 45    -> ALERTA
    ("ocupacao_confinamento", 0.88),  # > 0.85  -> AVALIAR
    ("taxa_prenhez", 0.79),           # < 0.82  -> REVISAR
    ("gmd", 1.60),                    # >= 1.55 -> OK
    ("capital_giro_dias", 120),       # >= 90   -> OK
]

VALORES_EXEMPLO_F2 = [
    ("custo_dieta_cab_dia", 12.80),   # OK
    ("estoque_silagem_dias", 60),     # OK
    ("taxa_prenhez", 0.85),           # OK
]

VALORES_EXEMPLO_F3 = [
    ("custo_dieta_cab_dia", 13.90),   # ALERTA
    ("gmd", 1.40),                    # REVISAR
    ("capital_giro_dias", 70),        # ALERTA
]


def run() -> None:
    db = SessionLocal()
    try:
        existe = db.execute(
            select(Organizacao).where(Organizacao.slug == "jln")
        ).scalar_one_or_none()
        if existe:
            print("Organizacao 'jln' ja existe — seed ignorado.")
            return

        org = Organizacao(nome="Grupo JLN", slug="jln")
        db.add(org)
        db.flush()

        fazendas = [
            Fazenda(org_id=org.id, nome="Fazenda Sede - Arapiraca", municipio="Arapiraca", uf="AL"),
            Fazenda(org_id=org.id, nome="Fazenda 2", municipio=None, uf="AL"),
            Fazenda(org_id=org.id, nome="Fazenda 3", municipio=None, uf="AL"),
        ]
        db.add_all(fazendas)
        db.flush()

        # premissas iguais para as 3 fazendas (partem do plano; editaveis por fazenda)
        for faz in fazendas:
            for grupo, chave, rotulo, valor, unidade in PREMISSAS:
                db.add(Parametro(
                    fazenda_id=faz.id, grupo=grupo, chave=chave,
                    rotulo=rotulo, valor=valor, unidade=unidade,
                ))

        # catalogo de indicadores (global)
        ind_por_codigo: dict[str, IndicadorDefinicao] = {}
        for codigo, nome, categoria, unidade, formato, casas in INDICADORES:
            ind = IndicadorDefinicao(
                codigo=codigo, nome=nome, categoria=categoria,
                unidade=unidade, formato=formato, casas_decimais=casas,
            )
            db.add(ind)
            ind_por_codigo[codigo] = ind
        db.flush()

        # regras da organizacao
        for (cod, nome, op, tipo, vfix, pchave, tol, sev, acao) in REGRAS:
            db.add(RegraGatilho(
                org_id=org.id, indicador_id=ind_por_codigo[cod].id, nome=nome,
                operador=op, tipo_referencia=tipo, valor_referencia=vfix,
                parametro_chave=pchave, tolerancia=tol, severidade=sev, acao=acao,
            ))

        # valores de exemplo
        hoje = date.today()
        for faz, valores in (
            (fazendas[0], VALORES_EXEMPLO_SEDE),
            (fazendas[1], VALORES_EXEMPLO_F2),
            (fazendas[2], VALORES_EXEMPLO_F3),
        ):
            for cod, valor in valores:
                db.add(IndicadorValor(
                    fazenda_id=faz.id, indicador_id=ind_por_codigo[cod].id,
                    valor=valor, data_ref=hoje, origem=OrigemValor.manual,
                ))

        # usuario admin (acesso as 3 fazendas)
        admin = Usuario(
            org_id=org.id, nome="Administrador", email=settings.admin_email,
            senha_hash=hash_senha(settings.admin_password), papel=PapelUsuario.admin,
        )
        db.add(admin)
        db.flush()
        for faz in fazendas:
            db.add(UsuarioFazenda(usuario_id=admin.id, fazenda_id=faz.id))

        db.commit()
        print("Seed concluido:")
        print(f"  Organizacao: {org.nome} (slug={org.slug})")
        print(f"  Fazendas: {', '.join(f.nome for f in fazendas)}")
        print(f"  Premissas por fazenda: {len(PREMISSAS)}")
        print(f"  Indicadores: {len(INDICADORES)} | Regras: {len(REGRAS)}")
        print(f"  Admin: {settings.admin_email} / (senha do .env)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
