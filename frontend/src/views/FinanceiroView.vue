<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Wallet, TrendingUp, TrendingDown, CalendarClock, Plus, Trash2 } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getFinanceiro, registrarLancamento, excluirLancamento,
  type Fazenda, type ResumoFinanceiro,
} from "../api";

const CATEGORIAS: Record<string, string[]> = {
  despesa: ["Nutrição", "Sanitário", "Mão de obra", "Insumos", "Manutenção", "Compra de animais", "Energia/Combustível", "Impostos", "Outros"],
  receita: ["Venda de animais", "Venda de leite", "Venda de bezerros", "Outros"],
};

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const dados = ref<ResumoFinanceiro | null>(null);
const erro = ref("");

const fmtData = (d: string) => d.split("-").reverse().join("/");
const fmtMoeda = (v: number) => `R$ ${v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const saldoTone = computed(() => ((dados.value?.saldo ?? 0) >= 0 ? "primary" : "danger"));
const giroTone = computed(() => {
  const d = dados.value?.capital_giro_dias;
  if (d === null || d === undefined) return "blue";
  return d >= 90 ? "primary" : d >= 60 ? "amber" : "danger";
});

const despesasPorCat = computed(() => dados.value?.categorias.filter((c) => c.tipo === "despesa") ?? []);
const receitasPorCat = computed(() => dados.value?.categorias.filter((c) => c.tipo === "receita") ?? []);
const maxDespesa = computed(() => Math.max(1, ...despesasPorCat.value.map((c) => c.total)));
const maxReceita = computed(() => Math.max(1, ...receitasPorCat.value.map((c) => c.total)));

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try { dados.value = await getFinanceiro(fazendaId.value); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  if (fazendas.value[0]) { fazendaId.value = fazendas.value[0].id; await carregar(); }
}
watch(fazendaId, (_v, old) => { if (old) carregar(); });
onMounted(init);

const modal = ref(false);
const form = ref({ tipo: "despesa" as "despesa" | "receita", categoria: "Nutrição", valor: "", data: "", descricao: "" });
const erroModal = ref("");
const salvando = ref(false);
function abrir(tipo: "despesa" | "receita") {
  form.value = { tipo, categoria: CATEGORIAS[tipo][0], valor: "", data: "", descricao: "" };
  erroModal.value = ""; modal.value = true;
}
watch(() => form.value.tipo, (t) => { form.value.categoria = CATEGORIAS[t][0]; });
async function salvar() {
  const v = parseFloat(form.value.valor.replace(",", "."));
  if (isNaN(v) || v <= 0) { erroModal.value = "Informe um valor positivo."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    await registrarLancamento(fazendaId.value, {
      tipo: form.value.tipo, categoria: form.value.categoria, valor: v,
      data: form.value.data || undefined, descricao: form.value.descricao || undefined,
    });
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
async function remover(id: string) {
  if (!confirm("Excluir este lançamento?")) return;
  try { await excluirLancamento(id); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell title="Financeiro" sub="Despesas, receitas e margem" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Resultado da fazenda</div>
      <h1>Financeiro</h1>
      <p>Lance <b>despesas</b> e <b>receitas</b>. O sistema calcula o saldo, a <b>margem por cabeça</b> e o <b>capital de giro</b> (em dias) — que abastecem o painel e o gatilho de caixa mínimo.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="Receitas" :value="fmtMoeda(dados.receitas)" sub="total acumulado" :icon="TrendingUp" tone="primary" />
      <KpiCard label="Despesas" :value="fmtMoeda(dados.despesas)" sub="total acumulado" :icon="TrendingDown" tone="danger" />
      <KpiCard label="Saldo" :value="fmtMoeda(dados.saldo)" sub="receitas − despesas" :icon="Wallet" :tone="saldoTone" />
      <KpiCard label="Margem / cabeça" :value="dados.margem_cab === null ? '—' : fmtMoeda(dados.margem_cab)"
               :sub="`${dados.n_animais} animais ativos`" emoji="🐂" tone="blue" />
      <KpiCard label="Capital de giro" :value="dados.capital_giro_dias === null ? '—' : `${dados.capital_giro_dias} d`"
               sub="caixa ÷ despesa diária" :icon="CalendarClock" :tone="giroTone" />
    </div>

    <div class="grid2" v-if="dados">
      <Panel title="Despesas por categoria" sub="onde o dinheiro sai">
        <div class="bars" v-if="despesasPorCat.length">
          <div class="barrow" v-for="c in despesasPorCat" :key="c.categoria">
            <div class="barlabel">{{ c.categoria }}</div>
            <div class="bartrack"><div class="barfill desp" :style="{ width: `${(c.total / maxDespesa) * 100}%` }" /></div>
            <div class="barval">{{ fmtMoeda(c.total) }}</div>
          </div>
        </div>
        <p v-else class="vazio">Sem despesas ainda.</p>
      </Panel>
      <Panel title="Receitas por categoria" sub="de onde o dinheiro entra">
        <div class="bars" v-if="receitasPorCat.length">
          <div class="barrow" v-for="c in receitasPorCat" :key="c.categoria">
            <div class="barlabel">{{ c.categoria }}</div>
            <div class="bartrack"><div class="barfill rec" :style="{ width: `${(c.total / maxReceita) * 100}%` }" /></div>
            <div class="barval">{{ fmtMoeda(c.total) }}</div>
          </div>
        </div>
        <p v-else class="vazio">Sem receitas ainda.</p>
      </Panel>
    </div>

    <Panel title="Lançamentos" sub="despesas e receitas recentes" v-if="dados">
      <template #actions>
        <div class="row" style="gap:8px">
          <button class="btn btn--secondary" style="height:34px" @click="abrir('despesa')"><Plus :size="15" /> Despesa</button>
          <button class="btn btn--primary" style="height:34px" @click="abrir('receita')"><Plus :size="15" /> Receita</button>
        </div>
      </template>
      <div class="tbl-wrap">
        <table class="tbl">
          <colgroup><col style="width:14%"/><col style="width:14%"/><col style="width:22%"/><col style="width:20%"/><col style="width:18%"/><col style="width:12%"/></colgroup>
          <thead><tr><th>Data</th><th>Tipo</th><th>Categoria</th><th class="num">Valor</th><th>Descrição</th><th class="num">Ações</th></tr></thead>
          <tbody>
            <tr v-for="l in dados.lancamentos" :key="l.id">
              <td>{{ fmtData(l.data) }}</td>
              <td>
                <span :class="['badge', l.tipo === 'receita' ? 'OK' : 'ALERTA']">
                  <span class="dot" /> {{ l.tipo === 'receita' ? 'Receita' : 'Despesa' }}
                </span>
              </td>
              <td>{{ l.categoria }}</td>
              <td class="num tnum">{{ fmtMoeda(l.valor) }}</td>
              <td class="muted">{{ l.descricao ?? "—" }}</td>
              <td class="num"><button class="iconbtn danger" @click="remover(l.id)"><Trash2 :size="14" /></button></td>
            </tr>
            <tr v-if="!dados.lancamentos.length"><td colspan="6" class="vazio">Nenhum lançamento ainda.</td></tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <Modal v-if="modal" :titulo="form.tipo === 'receita' ? 'Nova receita' : 'Nova despesa'"
           :sub="form.tipo === 'receita' ? 'entrada de dinheiro' : 'saída de dinheiro'" :largura="560" @fechar="modal = false">
      <div class="mform">
        <div class="two">
          <div class="field"><label>Tipo</label>
            <select class="input selc" v-model="form.tipo">
              <option value="despesa">Despesa</option>
              <option value="receita">Receita</option>
            </select>
          </div>
          <div class="field"><label>Categoria</label>
            <select class="input selc" v-model="form.categoria">
              <option v-for="c in CATEGORIAS[form.tipo]" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
        </div>
        <div class="two">
          <div class="field"><label>Valor (R$) *</label>
            <input class="input tnum" v-model="form.valor" placeholder="ex: 1500,00" @keyup.enter="salvar" />
          </div>
          <div class="field"><label>Data</label><input class="input" type="date" v-model="form.data" /></div>
        </div>
        <div class="field"><label>Descrição</label>
          <input class="input" v-model="form.descricao" placeholder="ex: Compra de ração, venda de 10 bois" />
        </div>
        <p v-if="erroModal" class="error">{{ erroModal }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modal = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvando" @click="salvar">Registrar</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.selc { width: auto; min-width: 200px; appearance: auto; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; margin-bottom: 16px; }
@media (max-width: 900px) { .grid2 { grid-template-columns: 1fr; } }
.bars { display: flex; flex-direction: column; gap: 12px; }
.barrow { display: grid; grid-template-columns: 130px 1fr auto; gap: 10px; align-items: center; }
.barlabel { font-size: 13px; color: var(--text); }
.bartrack { background: #eef2f4; border-radius: 999px; height: 12px; overflow: hidden; }
.barfill { height: 100%; border-radius: 999px; }
.barfill.desp { background: var(--danger); }
.barfill.rec { background: var(--primary); }
.barval { font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap; }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 620px; border-collapse: collapse; table-layout: fixed; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.mform { display: flex; flex-direction: column; gap: 13px; }
.mform .two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
</style>
