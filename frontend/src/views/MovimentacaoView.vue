<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ArrowLeftRight, TrendingDown, Skull, Plus, Trash2 } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getLotes, getAnimais, getMovimentos, getComposicao,
  registrarMovimentoAnimal, excluirMovimentoAnimal,
  type Fazenda, type Lote, type Animal, type ResumoMovimentos, type ComposicaoRebanho,
} from "../api";

const TIPOS = [
  { v: "compra", l: "Compra (entrada)" }, { v: "venda", l: "Venda (saída)" },
  { v: "descarte", l: "Descarte" }, { v: "morte", l: "Morte" }, { v: "transferencia", l: "Transferência de lote" },
];
const rot: Record<string, string> = { compra: "Compra", venda: "Venda", descarte: "Descarte", morte: "Morte", transferencia: "Transferência" };
const tone: Record<string, string> = { compra: "OK", venda: "AVALIAR", descarte: "REVISAR", morte: "ALERTA", transferencia: "OK" };

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const lotes = ref<Lote[]>([]);
const animais = ref<Animal[]>([]);
const mov = ref<ResumoMovimentos | null>(null);
const comp = ref<ComposicaoRebanho | null>(null);
const erro = ref("");
const fmtData = (d: string) => d.split("-").reverse().join("/");
const maxCat = computed(() => Math.max(1, ...(comp.value?.por_categoria ?? []).map((c) => c.total)));

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try {
    [mov.value, comp.value, lotes.value, animais.value] = await Promise.all([
      getMovimentos(fazendaId.value), getComposicao(fazendaId.value),
      getLotes(fazendaId.value), getAnimais(fazendaId.value),
    ]);
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  const sede = fazendas.value.find((f) => f.nome.includes("Sede")) ?? fazendas.value[0];
  if (sede) { fazendaId.value = sede.id; await carregar(); }
}
watch(fazendaId, (_v, old) => { if (old) carregar(); });
onMounted(init);

const ativos = computed(() => animais.value.filter((a) => a.status === "ativo"));
const modal = ref(false);
const form = ref({ animal_id: "", tipo: "venda", data: "", valor: "", motivo: "", lote_destino_id: "" });
const erroModal = ref("");
const salvando = ref(false);
function abrir() {
  form.value = { animal_id: "", tipo: "venda", data: "", valor: "", motivo: "", lote_destino_id: "" };
  erroModal.value = ""; modal.value = true;
}
async function salvar() {
  if (!form.value.animal_id) { erroModal.value = "Escolha o animal."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    await registrarMovimentoAnimal(form.value.animal_id, {
      tipo: form.value.tipo, data: form.value.data || undefined,
      valor: form.value.valor ? parseFloat(form.value.valor) : null,
      motivo: form.value.motivo || undefined,
      lote_destino_id: form.value.tipo === "transferencia" ? (form.value.lote_destino_id || null) : null,
    });
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
async function remover(id: string) {
  if (!confirm("Excluir este movimento? (não reverte o status do animal)")) return;
  try { await excluirMovimentoAnimal(id); await carregar(); } catch (e) { erro.value = String(e); }
}
</script>

<template>
  <AppShell title="Movimentação" sub="Entradas, saídas e descartes" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Rebanho</div>
      <h1>Movimentação de animais</h1>
      <p>Registre <b>compra, venda, morte, descarte</b> e <b>transferência de lote</b>. Cada movimento muda o status do animal e alimenta os indicadores do rebanho.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId"><option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option></select>
    </div>
    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="mov">
      <KpiCard label="Vendas (30 dias)" :value="mov.vendas_30d" sub="saídas" emoji="💵" tone="blue" />
      <KpiCard label="Descartes (30 dias)" :value="mov.descartes_30d" sub="marcados" :icon="TrendingDown" tone="amber" />
      <KpiCard label="Mortes (30 dias)" :value="mov.mortes_30d" sub="baixas" :icon="Skull" :tone="mov.mortes_30d ? 'danger' : 'primary'" />
      <KpiCard label="Compras (30 dias)" :value="mov.compras_30d" sub="entradas" :icon="ArrowLeftRight" tone="primary" />
    </div>

    <div class="grid2">
      <Panel title="Movimentos" sub="histórico de entradas/saídas" v-if="mov">
        <template #actions><button class="btn btn--primary" style="height:34px" @click="abrir"><Plus :size="15" /> Registrar movimento</button></template>
        <div class="tbl-wrap">
          <table class="tbl">
            <colgroup><col style="width:15%"/><col style="width:18%"/><col style="width:13%"/><col style="width:17%"/><col style="width:17%"/><col style="width:12%"/><col style="width:8%"/></colgroup>
            <thead><tr><th>Brinco</th><th>Tipo</th><th class="num">Valor</th><th>Motivo</th><th>Quem movimentou</th><th class="num">Data</th><th class="num"></th></tr></thead>
            <tbody>
              <tr v-for="m in mov.movimentos" :key="m.id">
                <td><strong>{{ m.brinco }}</strong></td>
                <td><span :class="['badge', tone[m.tipo]]"><span class="dot"/> {{ rot[m.tipo] }}</span></td>
                <td class="num tnum">{{ m.valor !== null ? "R$ " + m.valor.toFixed(2) : "—" }}</td>
                <td class="muted">{{ m.motivo ?? "—" }}</td>
                <td class="muted">{{ m.usuario_nome ?? "—" }}</td>
                <td class="num muted">{{ fmtData(m.data) }}</td>
                <td class="num"><button class="iconbtn danger" @click="remover(m.id)"><Trash2 :size="13"/></button></td>
              </tr>
              <tr v-if="!mov.movimentos.length"><td colspan="7" class="vazio">Nenhum movimento ainda.</td></tr>
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Composição do rebanho" :sub="comp ? `${comp.total} ativos · ${comp.femeas} fêmeas / ${comp.machos} machos` : ''" v-if="comp">
        <div class="bars">
          <div class="bar-row" v-for="c in comp.por_categoria" :key="c.categoria">
            <span class="bl">{{ c.categoria }}</span>
            <div class="bar"><span :style="{ width: (c.total / maxCat * 100) + '%' }" /></div>
            <b class="bv tnum">{{ c.total }}</b>
          </div>
          <div v-if="!comp.por_categoria.length" class="muted" style="padding:10px">Sem animais ativos.</div>
        </div>
      </Panel>
    </div>

    <Modal v-if="modal" titulo="Registrar movimento" sub="entrada, saída, descarte ou transferência" :largura="520" @fechar="modal = false">
      <div class="mform">
        <div class="field"><label>Animal *</label>
          <select class="input selc" v-model="form.animal_id"><option value="">— escolha —</option><option v-for="a in ativos" :key="a.id" :value="a.id">{{ a.brinco }} · {{ a.categoria }} {{ a.raca }}</option></select>
        </div>
        <div class="field"><label>Tipo de movimento</label>
          <select class="input selc" v-model="form.tipo"><option v-for="t in TIPOS" :key="t.v" :value="t.v">{{ t.l }}</option></select>
        </div>
        <div class="two">
          <div class="field" v-if="form.tipo === 'venda' || form.tipo === 'compra'"><label>Valor (R$)</label><input class="input tnum" type="number" step="0.01" v-model="form.valor" placeholder="ex: 6800" /></div>
          <div class="field" v-if="form.tipo === 'descarte' || form.tipo === 'morte'"><label>Motivo</label><input class="input" v-model="form.motivo" :placeholder="form.tipo==='descarte' ? 'ex: vaca vazia, idade' : 'ex: doença'" /></div>
          <div class="field" v-if="form.tipo === 'transferencia'"><label>Lote destino</label>
            <select class="input selc" v-model="form.lote_destino_id"><option value="">— escolha —</option><option v-for="l in lotes" :key="l.id" :value="l.id">{{ l.nome }}</option></select>
          </div>
          <div class="field"><label>Data</label><input class="input" type="date" v-model="form.data" /></div>
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
.grid2 { display: grid; grid-template-columns: 1.4fr 1fr; gap: 16px; align-items: start; }
@media (max-width: 900px) { .grid2 { grid-template-columns: 1fr; } }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 520px; border-collapse: collapse; table-layout: fixed; }
.tbl th, .tbl td { padding: 10px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.vazio { text-align: center; padding: 18px; color: var(--muted); }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted); width: 26px; height: 26px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.bars { padding: 4px 2px; }
.bar-row { display: grid; grid-template-columns: 90px 1fr 40px; align-items: center; gap: 10px; padding: 7px 0; }
.bl { font-size: 13.5px; }
.bar { height: 10px; background: #eef2f4; border-radius: 6px; overflow: hidden; }
.bar > span { display: block; height: 100%; background: var(--primary); border-radius: 6px; }
.bv { text-align: right; font-size: 13.5px; }
.mform { display: flex; flex-direction: column; gap: 13px; }
.mform .two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
</style>
