<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { DollarSign, RefreshCcw, Plus, Trash2, Package } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getMercado, criarArroba, buscarArroba, excluirArroba, criarInsumo, excluirInsumo,
  type Fazenda, type ResumoMercado,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const dados = ref<ResumoMercado | null>(null);
const erro = ref("");
const aviso = ref("");
const buscando = ref(false);

const fmtData = (d: string) => d.split("-").reverse().join("/");

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try { dados.value = await getMercado(fazendaId.value); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  const sede = fazendas.value.find((f) => f.nome.includes("Sede")) ?? fazendas.value[0];
  if (sede) { fazendaId.value = sede.id; await carregar(); }
}
watch(fazendaId, (_v, old) => { if (old) carregar(); });
onMounted(init);

async function buscar() {
  buscando.value = true; aviso.value = ""; erro.value = "";
  try {
    const r = await buscarArroba(fazendaId.value);
    aviso.value = r.encontrado
      ? `Arroba R$ ${r.valor?.toFixed(2)} buscada de ${r.fonte}.`
      : "Não foi possível buscar automaticamente. Informe a cotação manualmente.";
    if (r.encontrado) await carregar();
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
  finally { buscando.value = false; }
}

// modal arroba
const mArroba = ref(false);
const vArroba = ref("");
const erroA = ref("");
async function salvarArroba() {
  const v = parseFloat(vArroba.value);
  if (isNaN(v) || v <= 0) { erroA.value = "Informe o preço da arroba."; return; }
  try { await criarArroba(fazendaId.value, v); mArroba.value = false; vArroba.value = ""; await carregar(); }
  catch (e) { erroA.value = String(e instanceof Error ? e.message : e); }
}
async function delArroba(id: string) {
  if (!confirm("Excluir esta cotação?")) return;
  try { await excluirArroba(id); await carregar(); } catch (e) { erro.value = String(e); }
}

// modal insumo
const mInsumo = ref(false);
const fIns = ref({ insumo: "", praca: "", unidade: "kg", preco_origem: "", frete: "0", outros: "0", ms_pct: "0.88" });
const erroI = ref("");
function abrirInsumo() {
  fIns.value = { insumo: "", praca: "", unidade: "kg", preco_origem: "", frete: "0", outros: "0", ms_pct: "0.88" };
  erroI.value = ""; mInsumo.value = true;
}
async function salvarInsumo() {
  if (!fIns.value.insumo.trim()) { erroI.value = "Informe o insumo."; return; }
  const preco = parseFloat(fIns.value.preco_origem);
  if (isNaN(preco)) { erroI.value = "Informe o preço."; return; }
  try {
    await criarInsumo(fazendaId.value, {
      insumo: fIns.value.insumo, praca: fIns.value.praca || undefined, unidade: fIns.value.unidade,
      preco_origem: preco, frete: parseFloat(fIns.value.frete) || 0, outros: parseFloat(fIns.value.outros) || 0,
      ms_pct: parseFloat(fIns.value.ms_pct) || 1,
    });
    mInsumo.value = false; await carregar();
  } catch (e) { erroI.value = String(e instanceof Error ? e.message : e); }
}
async function delInsumo(id: string) {
  if (!confirm("Excluir este insumo?")) return;
  try { await excluirInsumo(id); await carregar(); } catch (e) { erro.value = String(e); }
}
</script>

<template>
  <AppShell title="Mercado & Custos" sub="Arroba e preços de insumos" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Mercado</div>
      <h1>Mercado & custos</h1>
      <p>Registre a <b>arroba do boi gordo</b> (R$/@) e os <b>preços dos insumos</b> — o sistema calcula o custo por kg de MS. A busca automática é <b>best-effort</b> (fonte externa instável); a cotação manual é a base confiável.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>
    <p v-if="aviso" class="aviso">{{ aviso }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="Arroba atual" :value="dados.arroba_atual === null ? '—' : `R$ ${dados.arroba_atual.toFixed(2)}`"
               :sub="dados.arroba_data ? fmtData(dados.arroba_data) : 'sem cotação'" :icon="DollarSign" tone="primary" />
      <KpiCard label="Insumos" :value="dados.insumos.length" sub="cotados" :icon="Package" tone="blue" />
      <KpiCard label="Cotações de arroba" :value="dados.historico.length" sub="no histórico" :icon="DollarSign" tone="amber" />
    </div>

    <div class="grid2" v-if="dados">
      <Panel title="Preços de insumos" sub="custo entregue → custo por kg de MS">
        <template #actions>
          <button class="btn btn--primary" style="height:34px" @click="abrirInsumo"><Plus :size="15" /> Novo insumo</button>
        </template>
        <div class="tbl-wrap">
          <table class="tbl">
            <colgroup><col style="width:26%"/><col style="width:22%"/><col style="width:18%"/><col style="width:22%"/><col style="width:12%"/></colgroup>
            <thead><tr><th>Insumo</th><th>Praça</th><th class="num">Entregue/kg</th><th class="num">Custo/kg MS</th><th class="num">Ações</th></tr></thead>
            <tbody>
              <tr v-for="i in dados.insumos" :key="i.id">
                <td><strong>{{ i.insumo }}</strong></td>
                <td class="muted">{{ i.praca ?? "—" }}</td>
                <td class="num tnum">R$ {{ i.custo_entregue_kg.toFixed(3) }}</td>
                <td class="num"><span class="badge AVALIAR"><span class="dot" /> R$ {{ i.custo_kg_ms?.toFixed(3) ?? "—" }}</span></td>
                <td class="num"><button class="iconbtn danger" @click="delInsumo(i.id)"><Trash2 :size="14" /></button></td>
              </tr>
              <tr v-if="!dados.insumos.length"><td colspan="5" class="vazio">Nenhum insumo cotado.</td></tr>
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Arroba do boi gordo" sub="R$ por arroba (@)">
        <template #actions>
          <div class="row" style="gap:8px">
            <button class="btn btn--secondary" style="height:34px" :disabled="buscando" @click="buscar"><RefreshCcw :size="14" /> {{ buscando ? "Buscando…" : "Buscar" }}</button>
            <button class="btn btn--primary" style="height:34px" @click="mArroba = true"><Plus :size="15" /> Nova</button>
          </div>
        </template>
        <div class="arroba-big" v-if="dados.arroba_atual !== null">
          R$ {{ dados.arroba_atual.toFixed(2) }} <span class="muted" style="font-size:14px">/@</span>
        </div>
        <div v-else class="muted" style="padding:8px 0">Sem cotação. Registre ou busque.</div>
        <div class="hist">
          <div class="hrow" v-for="a in dados.historico" :key="a.id">
            <span>{{ fmtData(a.data) }}</span>
            <b class="tnum">R$ {{ a.valor.toFixed(2) }}</b>
            <span class="tag" :class="{ auto: a.origem === 'integracao' }">{{ a.origem === 'integracao' ? 'auto' : 'manual' }}</span>
            <button class="iconbtn danger" @click="delArroba(a.id)"><Trash2 :size="13" /></button>
          </div>
        </div>
      </Panel>
    </div>

    <Modal v-if="mArroba" titulo="Nova cotação de arroba" sub="preço do boi gordo (R$/@)" @fechar="mArroba = false">
      <div class="mform">
        <div class="field"><label>Preço da arroba (R$/@) *</label>
          <input class="input tnum" type="number" step="0.01" v-model="vArroba" placeholder="ex: 310" @keyup.enter="salvarArroba" />
        </div>
        <p v-if="erroA" class="error">{{ erroA }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="mArroba = false">Cancelar</button>
        <button class="btn btn--primary" @click="salvarArroba">Salvar</button>
      </template>
    </Modal>

    <Modal v-if="mInsumo" titulo="Novo insumo" sub="preço entregue → custo por kg de MS" :largura="560" @fechar="mInsumo = false">
      <div class="mform">
        <div class="two">
          <div class="field"><label>Insumo *</label><input class="input" v-model="fIns.insumo" placeholder="ex: Milho moído" /></div>
          <div class="field"><label>Praça</label><input class="input" v-model="fIns.praca" placeholder="ex: Arapiraca/AL" /></div>
        </div>
        <div class="two">
          <div class="field"><label>Unidade</label>
            <select class="input selc" v-model="fIns.unidade"><option value="kg">kg</option><option value="t">tonelada</option></select>
          </div>
          <div class="field"><label>MS (0–1)</label><input class="input tnum" type="number" step="0.01" v-model="fIns.ms_pct" /></div>
        </div>
        <div class="three">
          <div class="field"><label>Preço origem</label><input class="input tnum" type="number" step="0.01" v-model="fIns.preco_origem" /></div>
          <div class="field"><label>Frete</label><input class="input tnum" type="number" step="0.01" v-model="fIns.frete" /></div>
          <div class="field"><label>Outros</label><input class="input tnum" type="number" step="0.01" v-model="fIns.outros" /></div>
        </div>
        <span class="hint">Custo entregue = preço + frete + outros. O custo por kg de MS divide pelo teor de matéria seca.</span>
        <p v-if="erroI" class="error">{{ erroI }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="mInsumo = false">Cancelar</button>
        <button class="btn btn--primary" @click="salvarInsumo">Salvar insumo</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.selc { width: auto; min-width: 160px; appearance: auto; }
.aviso { background: #eef5fb; border: 1px solid #cfe0f0; color: #1462a8; border-radius: 8px; padding: 9px 12px; font-size: 13.5px; }
.grid2 { display: grid; grid-template-columns: 1.4fr 1fr; gap: 16px; align-items: start; }
@media (max-width: 900px) { .grid2 { grid-template-columns: 1fr; } }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 480px; border-collapse: collapse; table-layout: fixed; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.arroba-big { font-size: 34px; font-weight: 800; color: var(--primary); padding: 4px 0 10px; }
.hist { display: flex; flex-direction: column; gap: 2px; }
.hrow { display: grid; grid-template-columns: 1fr auto auto 28px; align-items: center; gap: 10px; padding: 7px 0; border-top: 1px solid var(--border); font-size: 13.5px; }
.tag { font-size: 10.5px; font-weight: 700; padding: 2px 7px; border-radius: 5px; background: #eef2f4; color: #43555f; }
.tag.auto { background: #e6f0fb; color: #1462a8; }
.mform { display: flex; flex-direction: column; gap: 14px; }
.mform .two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
.mform .three { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; align-items: start; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
.mform .hint { font-size: 12px; color: var(--muted); }
</style>
