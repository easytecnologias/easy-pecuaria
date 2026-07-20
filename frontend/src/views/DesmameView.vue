<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Baby, Scale, Percent, Dna } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getDesmame, getAnimais, registrarDesmama, atualizarAnimal,
  TIPOS_MATRIZ,
  type Fazenda, type ResumoDesmama, type Animal,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const dados = ref<ResumoDesmama | null>(null);
const animais = ref<Animal[]>([]);
const erro = ref("");
const busca = ref("");

const pct = (v: number | null) => (v === null || v === undefined ? "—" : `${(v * 100).toFixed(1)}%`);
const fmtData = (d: string | null | undefined) => (d ? d.split("-").reverse().join("/") : "—");

// tom do KPI: verde se bateu a meta, âmbar se perto, vermelho se abaixo
function tone(valor: number | null, meta: number | null) {
  if (valor === null || meta === null) return "blue";
  return valor >= meta ? "primary" : valor >= meta * 0.9 ? "amber" : "danger";
}

const bezerros = computed(() => {
  let lista = animais.value.filter((a) => a.categoria === "Bezerro" && a.status === "ativo");
  const q = busca.value.trim().toLowerCase();
  if (q) lista = lista.filter((a) => (a.brinco ?? "").toLowerCase().includes(q) || (a.mae_brinco ?? "").toLowerCase().includes(q));
  return lista;
});
const matrizes = computed(() =>
  animais.value.filter((a) => ["Matriz", "Vaca"].includes(a.categoria ?? "") && a.status === "ativo")
);

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try {
    dados.value = await getDesmame(fazendaId.value);
    animais.value = await getAnimais(fazendaId.value);
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  if (fazendas.value[0]) { fazendaId.value = fazendas.value[0].id; await carregar(); }
}
watch(fazendaId, (_v, old) => { if (old) carregar(); });
onMounted(init);

// --- registrar desmama do bezerro ---
const modal = ref(false);
const alvo = ref<Animal | null>(null);
const peso = ref("");
const dataDesm = ref("");
const erroModal = ref("");
const salvando = ref(false);

function abrir(a: Animal) {
  alvo.value = a; peso.value = a.desmama_peso?.toString() ?? "";
  dataDesm.value = a.desmama_data ?? ""; erroModal.value = ""; modal.value = true;
}
async function salvar() {
  if (!alvo.value) return;
  const p = parseFloat(peso.value);
  if (isNaN(p) || p <= 0) { erroModal.value = "Informe o peso na desmama (kg)."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    await registrarDesmama(alvo.value.id, p, dataDesm.value || undefined);
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}

// --- tipo de matriz (Nelore puro, F1, T-Cross...) ---
async function mudarTipo(a: Animal, tipo: string) {
  try { await atualizarAnimal(a.id, { tipo_matriz: tipo || null } as any); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell title="Desmame" sub="Peso de desmama por bezerro e tipos de matriz" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Cria</div>
      <h1>Desmame e matrizes</h1>
      <p>O peso de desmama é lançado <b>por bezerro</b> (vinculado à matriz pelo brinco da mãe). O sistema calcula a <b>média</b> e a <b>taxa de desmama</b> e compara com as metas da fazenda.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="Matrizes" :value="dados.matrizes" sub="ativas no rebanho" :icon="Dna" tone="primary" />
      <KpiCard label="Bezerros" :value="dados.bezerros" :sub="`${dados.desmamados} já desmamados`" :icon="Baby" tone="blue" />
      <KpiCard label="Peso médio desmama"
               :value="dados.peso_medio_desmama === null ? '—' : `${dados.peso_medio_desmama} kg`"
               :sub="`meta ${dados.peso_desmama_meta ?? '—'} kg`" :icon="Scale"
               :tone="tone(dados.peso_medio_desmama, dados.peso_desmama_meta)" />
      <KpiCard label="Taxa de desmama" :value="pct(dados.taxa_desmama)"
               :sub="`meta ${pct(dados.taxa_desmama_meta)}`" :icon="Percent"
               :tone="tone(dados.taxa_desmama, dados.taxa_desmama_meta)" />
    </div>

    <Panel title="Composição das matrizes" sub="por tipo genético" v-if="dados && Object.keys(dados.por_tipo_matriz).length">
      <div class="barras">
        <div v-for="(qtd, tipo) in dados.por_tipo_matriz" :key="tipo" class="barra">
          <div class="barra__l"><span>{{ tipo }}</span><b class="tnum">{{ qtd }}</b></div>
          <div class="barra__t"><div class="barra__f" :style="{ width: `${(qtd / dados.matrizes) * 100}%` }" /></div>
        </div>
      </div>
    </Panel>

    <Panel title="Bezerros" sub="lance o peso na desmama de cada bezerro">
      <div class="filtros">
        <input class="input" v-model="busca" placeholder="Buscar por brinco do bezerro ou da mãe..." />
      </div>
      <div class="tbl-wrap">
        <table class="tbl">
          <thead>
            <tr><th>Bezerro</th><th>Mãe (matriz)</th><th>Nascimento</th><th class="num">Peso desmama</th><th>Data</th><th class="num">Ação</th></tr>
          </thead>
          <tbody>
            <tr v-for="b in bezerros" :key="b.id">
              <td><b>{{ b.brinco }}</b></td>
              <td class="muted">{{ b.mae_brinco ?? "—" }}</td>
              <td>{{ fmtData(b.data_nascimento) }}</td>
              <td class="num tnum">
                <span v-if="b.desmama_peso">{{ b.desmama_peso }} kg</span>
                <span v-else class="muted">—</span>
              </td>
              <td>{{ fmtData(b.desmama_data) }}</td>
              <td class="num">
                <button class="btn btn--secondary btnp" @click="abrir(b)">
                  {{ b.desmama_peso ? "Editar" : "Desmamar" }}
                </button>
              </td>
            </tr>
            <tr v-if="!bezerros.length"><td colspan="6" class="vazio">Nenhum bezerro ativo {{ busca ? "com essa busca" : "" }}.</td></tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <Panel title="Matrizes" sub="defina o tipo genético de cada matriz (Nelore puro, F1, T-Cross...)">
      <div class="tbl-wrap">
        <table class="tbl">
          <thead><tr><th>Brinco</th><th>Raça</th><th>Nascimento</th><th>Tipo de matriz</th></tr></thead>
          <tbody>
            <tr v-for="m in matrizes.slice(0, 100)" :key="m.id">
              <td><b>{{ m.brinco }}</b></td>
              <td class="muted">{{ m.raca ?? "—" }}</td>
              <td>{{ fmtData(m.data_nascimento) }}</td>
              <td>
                <select class="input selt" :value="m.tipo_matriz ?? ''"
                        @change="mudarTipo(m, ($event.target as HTMLSelectElement).value)">
                  <option value="">— não informado —</option>
                  <option v-for="t in TIPOS_MATRIZ" :key="t" :value="t">{{ t }}</option>
                </select>
              </td>
            </tr>
            <tr v-if="!matrizes.length"><td colspan="4" class="vazio">Nenhuma matriz cadastrada.</td></tr>
          </tbody>
        </table>
      </div>
      <p v-if="matrizes.length > 100" class="muted" style="font-size:12px;margin-top:8px">
        Mostrando as 100 primeiras de {{ matrizes.length }} matrizes.
      </p>
    </Panel>

    <Modal v-if="modal" titulo="Registrar desmama" :sub="`Bezerro ${alvo?.brinco}`" @fechar="modal = false">
      <div class="mform">
        <div class="field"><label>Peso na desmama (kg) *</label>
          <input class="input tnum peso" type="number" v-model="peso" placeholder="ex: 220" />
          <span class="hint">Entra na média de peso de desmama da fazenda.</span>
        </div>
        <div class="field"><label>Data</label>
          <input class="input" type="date" v-model="dataDesm" />
          <span class="hint">Em branco = hoje.</span>
        </div>
        <p v-if="erroModal" class="error">{{ erroModal }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modal = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvando" @click="salvar">Salvar</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.selc { width: auto; min-width: 200px; appearance: auto; }
.selt { height: 32px; padding: 4px 8px; appearance: auto; min-width: 160px; }
.filtros { display: flex; gap: 8px; margin-bottom: 12px; }
.filtros .input { flex: 1; }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 620px; border-collapse: collapse; }
.tbl th, .tbl td { padding: 10px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.btnp { height: 30px; padding: 0 12px; font-size: 13px; }
.barras { display: flex; flex-direction: column; gap: 10px; }
.barra__l { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
.barra__t { height: 8px; background: var(--bg); border-radius: 999px; overflow: hidden; }
.barra__f { height: 100%; background: var(--primary); border-radius: 999px; }
.mform { display: flex; flex-direction: column; gap: 14px; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
.mform .hint { font-size: 12px; color: var(--muted); }
.peso { font-size: 22px; height: 52px; font-weight: 700; }
</style>
