<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Printer, FileSpreadsheet, FileText } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import {
  getFazendas, getAnimais, getLotes, getFinanceiro,
  getRelatorioPesagem, getSanitario, getReproducao, getPartos,
  type Fazenda, type Animal, type Lote, type ResumoFinanceiro,
  type RelatorioPesagem, type ResumoSanitario, type ResumoReproducao, type ResumoPartos,
} from "../api";

type TipoRel = "rebanho" | "financeiro" | "pesagem" | "sanitario" | "reprodutivo";
const RELATORIOS: { id: TipoRel; label: string; emoji: string }[] = [
  { id: "rebanho", label: "Inventário do Rebanho", emoji: "📋" },
  { id: "pesagem", label: "Desempenho / Pesagem", emoji: "⚖️" },
  { id: "financeiro", label: "Financeiro", emoji: "💰" },
  { id: "sanitario", label: "Sanitário", emoji: "🩺" },
  { id: "reprodutivo", label: "Reprodutivo", emoji: "🧬" },
];

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const tipo = ref<TipoRel>("rebanho");
const erro = ref("");
const carregando = ref(false);

// dados
const animais = ref<Animal[]>([]);
const lotes = ref<Lote[]>([]);
const financeiro = ref<ResumoFinanceiro | null>(null);
const pesagem = ref<RelatorioPesagem | null>(null);
const sanitario = ref<ResumoSanitario | null>(null);
const reproducao = ref<ResumoReproducao | null>(null);
const partos = ref<ResumoPartos | null>(null);
const rotuloTipoSan: Record<string, string> = { vacina: "Vacina", vermifugo: "Vermífugo", tratamento: "Tratamento", exame: "Exame", carrapaticida: "Carrapaticida", hormonio: "Hormônio" };

const fazenda = computed(() => fazendas.value.find((f) => f.id === fazendaId.value));
const agora = computed(() => new Date().toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }));
const fmtData = (d: string | null) => (d ? d.split("-").reverse().join("/") : "—");
const fmtMoeda = (v: number) => `R$ ${v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const fmtPct = (v: number | null) => (v === null ? "—" : `${(v * 100).toFixed(1)}%`);

// ---- Inventário do rebanho (computado no cliente) ----
const ativos = computed(() => animais.value.filter((a) => a.status === "ativo"));
const nomeLote = (id: string | null) => (id ? lotes.value.find((l) => l.id === id)?.nome ?? "—" : "Sem lote");
function agrupar<T extends string>(chave: (a: Animal) => T) {
  const m: Record<string, number> = {};
  for (const a of ativos.value) { const k = chave(a) || "—"; m[k] = (m[k] ?? 0) + 1; }
  return Object.entries(m).sort((x, y) => y[1] - x[1]);
}
const porCategoria = computed(() => agrupar((a) => a.categoria ?? "—"));
const porSexo = computed(() => agrupar((a) => (a.sexo === "F" ? "Fêmeas" : a.sexo === "M" ? "Machos" : "—")));
const porLote = computed(() => agrupar((a) => nomeLote(a.lote_id)));

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = ""; carregando.value = true;
  try {
    const fid = fazendaId.value;
    if (tipo.value === "rebanho") {
      [animais.value, lotes.value] = await Promise.all([getAnimais(fid), getLotes(fid)]);
    } else if (tipo.value === "financeiro") {
      financeiro.value = await getFinanceiro(fid);
    } else if (tipo.value === "pesagem") {
      pesagem.value = await getRelatorioPesagem(fid);
    } else if (tipo.value === "sanitario") {
      sanitario.value = await getSanitario(fid);
    } else if (tipo.value === "reprodutivo") {
      [reproducao.value, partos.value] = await Promise.all([getReproducao(fid), getPartos(fid)]);
    }
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
  finally { carregando.value = false; }
}
async function init() {
  fazendas.value = await getFazendas();
  if (fazendas.value[0]) { fazendaId.value = fazendas.value[0].id; await carregar(); }
}
watch([fazendaId, tipo], carregar);
onMounted(init);

function imprimir() { window.print(); }

function baixarCSV(nome: string, linhas: (string | number)[][]) {
  const csv = linhas.map((l) => l.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(";")).join("\r\n");
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = nome;
  a.click();
  URL.revokeObjectURL(a.href);
}
function exportarExcel() {
  const nomeFaz = (fazenda.value?.nome ?? "fazenda").replace(/\s+/g, "-").toLowerCase();
  if (tipo.value === "rebanho") {
    const linhas: (string | number)[][] = [["Brinco", "Categoria", "Raça", "Sexo", "Nascimento", "Lote", "Status"]];
    for (const a of animais.value) {
      linhas.push([a.brinco, a.categoria ?? "", a.raca ?? "", a.sexo ?? "", fmtData(a.data_nascimento), nomeLote(a.lote_id), a.status]);
    }
    baixarCSV(`rebanho-${nomeFaz}.csv`, linhas);
  } else if (tipo.value === "financeiro" && financeiro.value) {
    const linhas: (string | number)[][] = [["Data", "Tipo", "Categoria", "Valor", "Descrição"]];
    for (const l of financeiro.value.lancamentos) linhas.push([fmtData(l.data), l.tipo, l.categoria, l.valor, l.descricao ?? ""]);
    baixarCSV(`financeiro-${nomeFaz}.csv`, linhas);
  } else if (tipo.value === "pesagem" && pesagem.value) {
    const linhas: (string | number)[][] = [["Brinco", "Categoria", "Lote", "Peso (kg)", "Data", "GMD (kg/dia)"]];
    for (const a of pesagem.value.animais) linhas.push([a.brinco, a.categoria ?? "", a.lote ?? "", a.peso, fmtData(a.data), a.gmd ?? ""]);
    baixarCSV(`pesagem-${nomeFaz}.csv`, linhas);
  } else if (tipo.value === "sanitario" && sanitario.value) {
    const linhas: (string | number)[][] = [["Brinco", "Tipo", "Produto", "Data", "Próxima", "Dose"]];
    for (const h of sanitario.value.historico) linhas.push([h.brinco, rotuloTipoSan[h.tipo] ?? h.tipo, h.produto, fmtData(h.data), fmtData(h.proxima), h.dose ?? ""]);
    baixarCSV(`sanitario-${nomeFaz}.csv`, linhas);
  } else if (tipo.value === "reprodutivo" && reproducao.value) {
    const linhas: (string | number)[][] = [["Brinco", "Touro", "Inseminador", "Data", "Resultado"]];
    for (const i of reproducao.value.inseminacoes) linhas.push([i.animal_brinco, i.touro, i.inseminador ?? "", fmtData(i.data), i.resultado]);
    baixarCSV(`reprodutivo-${nomeFaz}.csv`, linhas);
  }
}
</script>

<template>
  <AppShell title="Relatórios" sub="Imprimir e exportar" @refresh="carregar">
    <div class="head no-print">
      <div class="eyebrow">Saídas</div>
      <h1>Relatórios</h1>
      <p>Gere relatórios prontos para <b>imprimir/salvar em PDF</b> ou <b>exportar para Excel</b>. Escolha o tipo, a fazenda e clique em gerar.</p>
    </div>

    <div class="controls no-print">
      <div class="seg">
        <button v-for="r in RELATORIOS" :key="r.id" class="segbtn" :class="{ on: tipo === r.id }" @click="tipo = r.id">
          {{ r.emoji }} {{ r.label }}
        </button>
      </div>
      <div class="row" style="gap:10px;flex-wrap:wrap">
        <select class="input selc" v-model="fazendaId">
          <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
        </select>
        <button class="btn btn--secondary" @click="exportarExcel"><FileSpreadsheet :size="16" /> Excel</button>
        <button class="btn btn--primary" @click="imprimir"><Printer :size="16" /> Imprimir / PDF</button>
      </div>
    </div>

    <p v-if="erro" class="error no-print">{{ erro }}</p>

    <!-- FOLHA DO RELATÓRIO (o que é impresso) -->
    <div class="folha">
      <div class="folha-cab">
        <div>
          <div class="folha-org">Grupo JLN · Sistema Pecuária</div>
          <div class="folha-tit">{{ RELATORIOS.find(r => r.id === tipo)?.label }}</div>
          <div class="folha-sub">{{ fazenda?.nome }} <span v-if="fazenda?.uf">· {{ fazenda?.municipio ? fazenda.municipio + '/' : '' }}{{ fazenda?.uf }}</span></div>
        </div>
        <div class="folha-meta"><FileText :size="14" /> Gerado em {{ agora }}</div>
      </div>

      <!-- REBANHO -->
      <template v-if="tipo === 'rebanho'">
        <div class="tot">Total de animais ativos: <b>{{ ativos.length }}</b></div>
        <div class="grid3">
          <div class="bloco">
            <h3>Por categoria</h3>
            <table class="rtbl"><tbody>
              <tr v-for="[k, n] in porCategoria" :key="k"><td>{{ k }}</td><td class="num">{{ n }}</td></tr>
            </tbody></table>
          </div>
          <div class="bloco">
            <h3>Por sexo</h3>
            <table class="rtbl"><tbody>
              <tr v-for="[k, n] in porSexo" :key="k"><td>{{ k }}</td><td class="num">{{ n }}</td></tr>
            </tbody></table>
          </div>
          <div class="bloco">
            <h3>Por lote</h3>
            <table class="rtbl"><tbody>
              <tr v-for="[k, n] in porLote" :key="k"><td>{{ k }}</td><td class="num">{{ n }}</td></tr>
            </tbody></table>
          </div>
        </div>

        <h3 class="lista-tit">Relação de animais ({{ animais.length }})</h3>
        <table class="rtbl full">
          <thead><tr><th>Brinco</th><th>Categoria</th><th>Raça</th><th>Sexo</th><th>Nascimento</th><th>Lote</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-for="a in animais" :key="a.id">
              <td><b>{{ a.brinco }}</b></td><td>{{ a.categoria ?? "—" }}</td><td>{{ a.raca ?? "—" }}</td>
              <td>{{ a.sexo ?? "—" }}</td><td>{{ fmtData(a.data_nascimento) }}</td><td>{{ nomeLote(a.lote_id) }}</td>
              <td>{{ a.status }}</td>
            </tr>
            <tr v-if="!animais.length"><td colspan="7" class="vazio">Sem animais.</td></tr>
          </tbody>
        </table>
      </template>

      <!-- FINANCEIRO -->
      <template v-else-if="tipo === 'financeiro' && financeiro">
        <div class="kpis">
          <div class="kpi"><span>Receitas</span><b class="pos">{{ fmtMoeda(financeiro.receitas) }}</b></div>
          <div class="kpi"><span>Despesas</span><b class="neg">{{ fmtMoeda(financeiro.despesas) }}</b></div>
          <div class="kpi"><span>Saldo</span><b :class="financeiro.saldo >= 0 ? 'pos' : 'neg'">{{ fmtMoeda(financeiro.saldo) }}</b></div>
          <div class="kpi"><span>Margem / cabeça</span><b>{{ financeiro.margem_cab === null ? '—' : fmtMoeda(financeiro.margem_cab) }}</b></div>
          <div class="kpi"><span>Capital de giro</span><b>{{ financeiro.capital_giro_dias === null ? '—' : financeiro.capital_giro_dias + ' d' }}</b></div>
        </div>
        <div class="grid2">
          <div class="bloco">
            <h3>Despesas por categoria</h3>
            <table class="rtbl"><tbody>
              <tr v-for="c in financeiro.categorias.filter(c => c.tipo === 'despesa')" :key="c.categoria"><td>{{ c.categoria }}</td><td class="num">{{ fmtMoeda(c.total) }}</td></tr>
              <tr v-if="!financeiro.categorias.some(c => c.tipo === 'despesa')"><td class="vazio" colspan="2">Sem despesas.</td></tr>
            </tbody></table>
          </div>
          <div class="bloco">
            <h3>Receitas por categoria</h3>
            <table class="rtbl"><tbody>
              <tr v-for="c in financeiro.categorias.filter(c => c.tipo === 'receita')" :key="c.categoria"><td>{{ c.categoria }}</td><td class="num">{{ fmtMoeda(c.total) }}</td></tr>
              <tr v-if="!financeiro.categorias.some(c => c.tipo === 'receita')"><td class="vazio" colspan="2">Sem receitas.</td></tr>
            </tbody></table>
          </div>
        </div>

        <h3 class="lista-tit">Lançamentos ({{ financeiro.lancamentos.length }})</h3>
        <table class="rtbl full">
          <thead><tr><th>Data</th><th>Tipo</th><th>Categoria</th><th class="num">Valor</th><th>Descrição</th></tr></thead>
          <tbody>
            <tr v-for="l in financeiro.lancamentos" :key="l.id">
              <td>{{ fmtData(l.data) }}</td><td>{{ l.tipo === 'receita' ? 'Receita' : 'Despesa' }}</td>
              <td>{{ l.categoria }}</td><td class="num">{{ fmtMoeda(l.valor) }}</td><td>{{ l.descricao ?? "—" }}</td>
            </tr>
            <tr v-if="!financeiro.lancamentos.length"><td colspan="5" class="vazio">Sem lançamentos.</td></tr>
          </tbody>
        </table>
      </template>

      <!-- PESAGEM / DESEMPENHO -->
      <template v-else-if="tipo === 'pesagem' && pesagem">
        <div class="kpis">
          <div class="kpi"><span>Animais pesados</span><b>{{ pesagem.com_pesagem }} / {{ pesagem.total }}</b></div>
          <div class="kpi"><span>Peso médio</span><b>{{ pesagem.peso_medio === null ? '—' : pesagem.peso_medio + ' kg' }}</b></div>
          <div class="kpi"><span>@ média</span><b>{{ pesagem.arroba_media === null ? '—' : pesagem.arroba_media + ' @' }}</b></div>
          <div class="kpi"><span>GMD médio</span><b>{{ pesagem.gmd_medio === null ? '—' : pesagem.gmd_medio + ' kg/dia' }}</b></div>
        </div>
        <h3 class="lista-tit">Última pesagem por animal ({{ pesagem.com_pesagem }})</h3>
        <table class="rtbl full">
          <thead><tr><th>Brinco</th><th>Categoria</th><th>Lote</th><th class="num">Peso (kg)</th><th>Data</th><th class="num">GMD (kg/dia)</th></tr></thead>
          <tbody>
            <tr v-for="(a, i) in pesagem.animais" :key="i">
              <td><b>{{ a.brinco }}</b></td><td>{{ a.categoria ?? "—" }}</td><td>{{ a.lote ?? "—" }}</td>
              <td class="num">{{ a.peso }}</td><td>{{ fmtData(a.data) }}</td><td class="num">{{ a.gmd ?? "—" }}</td>
            </tr>
            <tr v-if="!pesagem.animais.length"><td colspan="6" class="vazio">Nenhum animal com pesagem registrada.</td></tr>
          </tbody>
        </table>
      </template>

      <!-- SANITÁRIO -->
      <template v-else-if="tipo === 'sanitario' && sanitario">
        <div class="kpis">
          <div class="kpi"><span>Aplicações registradas</span><b>{{ sanitario.total }}</b></div>
          <div class="kpi"><span>Vencendo (15 dias)</span><b :class="sanitario.vencendo ? 'neg' : ''">{{ sanitario.vencendo }}</b></div>
        </div>
        <h3 class="lista-tit">Agenda — próximas aplicações</h3>
        <table class="rtbl full">
          <thead><tr><th>Produto</th><th>Tipo</th><th class="num">Animais</th><th class="num">Próxima</th></tr></thead>
          <tbody>
            <tr v-for="(a, i) in sanitario.agenda" :key="i">
              <td><b>{{ a.produto }}</b></td><td>{{ rotuloTipoSan[a.tipo] ?? a.tipo }}</td>
              <td class="num">{{ a.animais }}</td><td class="num" :class="a.vencido ? 'neg' : ''">{{ fmtData(a.proxima) }}</td>
            </tr>
            <tr v-if="!sanitario.agenda.length"><td colspan="4" class="vazio">Nada agendado.</td></tr>
          </tbody>
        </table>
        <h3 class="lista-tit">Histórico de aplicações ({{ sanitario.historico.length }})</h3>
        <table class="rtbl full">
          <thead><tr><th>Brinco</th><th>Produto</th><th>Tipo</th><th>Data</th><th>Dose</th></tr></thead>
          <tbody>
            <tr v-for="h in sanitario.historico" :key="h.id">
              <td><b>{{ h.brinco }}</b></td><td>{{ h.produto }}</td><td>{{ rotuloTipoSan[h.tipo] ?? h.tipo }}</td>
              <td>{{ fmtData(h.data) }}</td><td>{{ h.dose ?? "—" }}</td>
            </tr>
            <tr v-if="!sanitario.historico.length"><td colspan="5" class="vazio">Sem registros.</td></tr>
          </tbody>
        </table>
      </template>

      <!-- REPRODUTIVO -->
      <template v-else-if="tipo === 'reprodutivo' && reproducao">
        <div class="kpis">
          <div class="kpi"><span>Taxa de prenhez</span><b>{{ fmtPct(reproducao.taxa_prenhez) }}</b></div>
          <div class="kpi"><span>Prenhes / Vazias</span><b>{{ reproducao.prenhes }} / {{ reproducao.vazias }}</b></div>
          <div class="kpi"><span>Partos (12 m)</span><b>{{ partos?.partos_12m ?? 0 }}</b></div>
          <div class="kpi"><span>Natalidade</span><b>{{ fmtPct(partos?.taxa_natalidade ?? null) }}</b></div>
        </div>
        <h3 class="lista-tit">Prenhez por touro</h3>
        <table class="rtbl full">
          <thead><tr><th>Touro</th><th class="num">IATF</th><th class="num">Prenhes</th><th class="num">Vazias</th><th class="num">Taxa</th></tr></thead>
          <tbody>
            <tr v-for="(g, i) in reproducao.por_touro" :key="i">
              <td><b>{{ g.nome }}</b></td><td class="num">{{ g.total }}</td><td class="num">{{ g.prenhes }}</td>
              <td class="num">{{ g.vazias }}</td><td class="num">{{ fmtPct(g.taxa) }}</td>
            </tr>
            <tr v-if="!reproducao.por_touro.length"><td colspan="5" class="vazio">Sem inseminações.</td></tr>
          </tbody>
        </table>
        <h3 class="lista-tit">Partos ({{ partos?.partos.length ?? 0 }})</h3>
        <table class="rtbl full">
          <thead><tr><th>Data</th><th>Mãe</th><th>Bezerro</th><th>Sexo</th><th>Resultado</th></tr></thead>
          <tbody>
            <tr v-for="p in partos?.partos ?? []" :key="p.id">
              <td>{{ fmtData(p.data) }}</td><td><b>{{ p.mae_brinco }}</b></td><td>{{ p.brinco_bezerro ?? "—" }}</td>
              <td>{{ p.sexo_bezerro ?? "—" }}</td><td>{{ p.resultado === 'nascido_vivo' ? 'Nascido vivo' : 'Natimorto' }}</td>
            </tr>
            <tr v-if="!(partos?.partos.length)"><td colspan="5" class="vazio">Sem partos registrados.</td></tr>
          </tbody>
        </table>
      </template>

      <p v-if="carregando" class="vazio">Carregando…</p>
    </div>
  </AppShell>
</template>

<style scoped>
.controls { display: flex; justify-content: space-between; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 18px; }
.seg { display: inline-flex; background: #eef2f4; border-radius: 10px; padding: 4px; gap: 4px; }
.segbtn { border: none; background: transparent; padding: 8px 14px; border-radius: 8px; font-size: 13.5px; font-weight: 600; color: var(--muted); cursor: pointer; }
.segbtn.on { background: var(--surface); color: var(--text); box-shadow: var(--shadow); }
.selc { width: auto; min-width: 200px; appearance: auto; }

.folha { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 32px; box-shadow: var(--shadow); }
.folha-cab { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid var(--text); padding-bottom: 14px; margin-bottom: 18px; }
.folha-org { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
.folha-tit { font-size: 22px; font-weight: 800; margin-top: 2px; }
.folha-sub { font-size: 14px; color: var(--muted); margin-top: 2px; }
.folha-meta { font-size: 12px; color: var(--muted); display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
.tot { font-size: 15px; margin-bottom: 14px; }
.grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin-bottom: 8px; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin: 14px 0 8px; }
.kpis { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 10px; }
.kpi { border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; }
.kpi span { font-size: 11.5px; color: var(--muted); display: block; }
.kpi b { font-size: 16px; }
.bloco h3, .lista-tit { font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); margin: 0 0 8px; }
.lista-tit { margin-top: 20px; }
.pos { color: var(--primary); } .neg { color: var(--danger); }
.rtbl { width: 100%; border-collapse: collapse; font-size: 13px; }
.rtbl td, .rtbl th { padding: 6px 8px; text-align: left; border-bottom: 1px solid var(--border); }
.rtbl th { font-size: 11px; text-transform: uppercase; color: var(--muted); }
.rtbl .num { text-align: right; font-variant-numeric: tabular-nums; }
.rtbl.full { margin-top: 6px; }
.vazio { text-align: center; color: var(--muted); padding: 14px; }
@media (max-width: 900px) { .grid3, .grid2, .kpis { grid-template-columns: 1fr 1fr; } }
</style>
