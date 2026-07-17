<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Utensils, Plus, Trash2, X } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getLotes, getDietas, criarDieta, excluirDieta,
  type Fazenda, type Lote, type Dieta, type ItemDieta,
} from "../api";

const META_CUSTO = 13.5;
const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const lotes = ref<Lote[]>([]);
const dietas = ref<Dieta[]>([]);
const erro = ref("");

const fmtData = (d: string) => d.split("-").reverse().join("/");
const custoTone = (c: number) => (c <= META_CUSTO ? "OK" : "ALERTA");
const custoAtiva = computed(() => (dietas.value.length ? dietas.value[0].custo_cab_dia : null));

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try {
    [dietas.value, lotes.value] = await Promise.all([getDietas(fazendaId.value), getLotes(fazendaId.value)]);
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  const sede = fazendas.value.find((f) => f.nome.includes("Sede")) ?? fazendas.value[0];
  if (sede) { fazendaId.value = sede.id; await carregar(); }
}
watch(fazendaId, (_v, old) => { if (old) carregar(); });
onMounted(init);

// modal nova dieta
const modal = ref(false);
const form = ref<{ nome: string; lote_id: string; itens: ItemDieta[] }>({ nome: "", lote_id: "", itens: [] });
const erroModal = ref("");
const salvando = ref(false);

function abrir() {
  form.value = {
    nome: "", lote_id: "",
    itens: [{ ingrediente: "", inclusao_kg: 0, preco_kg: 0, ms_pct: 0.34 }],
  };
  erroModal.value = ""; modal.value = true;
}
function addItem() { form.value.itens.push({ ingrediente: "", inclusao_kg: 0, preco_kg: 0, ms_pct: 0.88 }); }
function removeItem(i: number) { form.value.itens.splice(i, 1); }

const custoPreview = computed(() =>
  form.value.itens.reduce((s, i) => s + (Number(i.inclusao_kg) || 0) * (Number(i.preco_kg) || 0), 0)
);

async function salvar() {
  if (!form.value.nome.trim()) { erroModal.value = "Dê um nome à dieta."; return; }
  const itens = form.value.itens.filter((i) => i.ingrediente.trim() && Number(i.inclusao_kg) > 0);
  if (!itens.length) { erroModal.value = "Adicione ao menos um ingrediente com inclusão."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    await criarDieta(fazendaId.value, {
      nome: form.value.nome, lote_id: form.value.lote_id || null,
      itens: itens.map((i) => ({
        ingrediente: i.ingrediente, inclusao_kg: Number(i.inclusao_kg),
        preco_kg: Number(i.preco_kg), ms_pct: Number(i.ms_pct),
      })),
    });
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
async function remover(id: string) {
  if (!confirm("Excluir esta dieta?")) return;
  try { await excluirDieta(id); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell title="Nutrição" sub="Dietas e custo/cab/dia" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Dieta</div>
      <h1>Nutrição · dietas por lote</h1>
      <p>Monte a dieta com os ingredientes (inclusão, preço, MS). O sistema calcula o <b>custo por cabeça/dia</b> e o consumo de MS — se o custo passar da meta (R$ {{ META_CUSTO }}), vira alerta.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics">
      <KpiCard label="Custo da dieta ativa" :value="custoAtiva === null ? '—' : `R$ ${custoAtiva.toFixed(2)}`"
               :sub="`meta R$ ${META_CUSTO}`" emoji="🥗"
               :tone="custoAtiva === null ? 'blue' : (custoAtiva <= META_CUSTO ? 'primary' : 'danger')" />
      <KpiCard label="Dietas cadastradas" :value="dietas.length" sub="por lote" :icon="Utensils" tone="amber" />
    </div>

    <Panel title="Dietas" sub="custo calculado dos ingredientes">
      <template #actions>
        <button class="btn btn--primary" style="height:34px" @click="abrir"><Plus :size="15" /> Nova dieta</button>
      </template>
      <div class="tbl-wrap">
        <table class="tbl">
          <colgroup><col style="width:26%"/><col style="width:22%"/><col style="width:16%"/><col style="width:16%"/><col style="width:10%"/><col style="width:10%"/></colgroup>
          <thead><tr><th>Dieta</th><th>Lote</th><th class="num">Custo/cab/dia</th><th class="num">Consumo MS</th><th class="num">Itens</th><th class="num">Ações</th></tr></thead>
          <tbody>
            <tr v-for="d in dietas" :key="d.id">
              <td><strong>{{ d.nome }}</strong><div class="muted sub">{{ fmtData(d.data) }}</div></td>
              <td class="muted">{{ d.lote_nome ?? "—" }}</td>
              <td class="num">
                <span :class="['badge', custoTone(d.custo_cab_dia)]"><span class="dot" /> R$ {{ d.custo_cab_dia.toFixed(2) }}</span>
              </td>
              <td class="num tnum muted">{{ d.consumo_ms_pv === null ? "—" : (d.consumo_ms_pv * 100).toFixed(1) + "% PV" }}</td>
              <td class="num tnum">{{ d.itens.length }}</td>
              <td class="num"><button class="iconbtn danger" @click="remover(d.id)"><Trash2 :size="14" /></button></td>
            </tr>
            <tr v-if="!dietas.length"><td colspan="6" class="vazio">Nenhuma dieta. Clique em "Nova dieta".</td></tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <Modal v-if="modal" titulo="Nova dieta" sub="ingredientes por cabeça/dia" :largura="640" @fechar="modal = false">
      <div class="mform">
        <div class="two">
          <div class="field"><label>Nome da dieta *</label>
            <input class="input" v-model="form.nome" placeholder="ex: Terminação confinamento" />
          </div>
          <div class="field"><label>Lote</label>
            <select class="input selc" v-model="form.lote_id">
              <option value="">— sem lote —</option>
              <option v-for="l in lotes" :key="l.id" :value="l.id">{{ l.nome }}</option>
            </select>
          </div>
        </div>

        <div class="itens">
          <div class="ihead"><span>Ingrediente</span><span>Inclusão (kg)</span><span>Preço (R$/kg)</span><span>MS (0–1)</span><span></span></div>
          <div class="irow" v-for="(it, i) in form.itens" :key="i">
            <input class="input" v-model="it.ingrediente" placeholder="ex: Silagem de milho" />
            <input class="input tnum" type="number" step="0.1" v-model.number="it.inclusao_kg" />
            <input class="input tnum" type="number" step="0.01" v-model.number="it.preco_kg" />
            <input class="input tnum" type="number" step="0.01" v-model.number="it.ms_pct" />
            <button class="iconbtn" @click="removeItem(i)"><X :size="14" /></button>
          </div>
          <button class="btn btn--secondary" style="height:32px;margin-top:6px" @click="addItem"><Plus :size="14" /> Adicionar ingrediente</button>
        </div>

        <div class="preview">
          Custo estimado: <b>R$ {{ custoPreview.toFixed(2) }}</b> /cab/dia
          <span :class="['badge', custoPreview <= META_CUSTO ? 'OK' : 'ALERTA']" style="margin-left:8px">
            <span class="dot" /> {{ custoPreview <= META_CUSTO ? "dentro da meta" : "acima da meta" }}
          </span>
        </div>
        <p v-if="erroModal" class="error">{{ erroModal }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modal = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvando" @click="salvar">Salvar dieta</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.selc { width: auto; min-width: 220px; appearance: auto; }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 560px; border-collapse: collapse; table-layout: fixed; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.tbl .sub { font-size: 12px; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }

.mform { display: flex; flex-direction: column; gap: 14px; }
.mform .two { display: grid; grid-template-columns: 1.4fr 1fr; gap: 12px; align-items: start; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
.itens { border: 1px solid var(--border); border-radius: 9px; padding: 10px; }
.ihead, .irow { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 30px; gap: 8px; align-items: center; }
.ihead { font-size: 11px; text-transform: uppercase; letter-spacing: .03em; color: var(--muted); margin-bottom: 6px; padding: 0 2px; }
.irow { margin-bottom: 6px; }
.irow .input { height: 34px; }
.preview { background: #f2f8f5; border: 1px solid #cfe6da; border-radius: 8px; padding: 10px 12px; font-size: 13.5px; color: #245c47; }
</style>
