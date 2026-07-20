<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Layers, Droplets, CalendarClock, Plus, Pencil, Trash2, AlertTriangle, PackageMinus } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getSilagem, criarSilagem, editarSilagem, excluirSilagem,
  TIPOS_SILAGEM,
  type Fazenda, type ResumoSilagem, type Silagem,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const dados = ref<ResumoSilagem | null>(null);
const erro = ref("");

const fmtData = (d: string | null) => (d ? d.split("-").reverse().join("/") : "—");
const rotTipo = (t: string) => TIPOS_SILAGEM.find((x) => x.valor === t)?.rotulo ?? t;
const pct = (v: number | null) => (v === null || v === undefined ? "—" : `${(v * 100).toFixed(1)}%`);

// MS fora do alvo (>3 pontos de diferença) = risco de perda no silo
const msTone = computed(() => {
  const d = dados.value;
  if (!d || d.ms_media === null || d.ms_alvo === null) return "blue";
  return Math.abs(d.ms_media - d.ms_alvo) <= 0.03 ? "primary" : "amber";
});
function foraDoAlvo(s: Silagem) {
  if (s.ms_real === null || !dados.value?.ms_alvo) return false;
  return Math.abs(s.ms_real - dados.value.ms_alvo) > 0.03;
}
// audio 3: silo que ja encostou no estoque de seguranca
function noMinimo(s: Silagem) {
  if (s.estoque_seguranca_t === null || s.quantidade_t === null) return false;
  return s.quantidade_t <= s.estoque_seguranca_t;
}

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try { dados.value = await getSilagem(fazendaId.value); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  if (fazendas.value[0]) { fazendaId.value = fazendas.value[0].id; await carregar(); }
}
watch(fazendaId, (_v, old) => { if (old) carregar(); });
onMounted(init);

const modal = ref(false);
const editando = ref<Silagem | null>(null);
const vazio = {
  nome: "", tipo: "milho", data_ensilagem: "", ms_meta: "", ms_real: "", umidade: "",
  temperatura: "", quantidade_t: "", consumo_diario_t: "", estoque_seguranca_t: "",
  maquinario: "", destino: "", responsavel: "", observacao: "", situacao: "aberto",
};
const form = ref({ ...vazio });
const erroModal = ref("");
const salvando = ref(false);

function abrirNovo() { editando.value = null; form.value = { ...vazio }; erroModal.value = ""; modal.value = true; }
function abrirEdicao(s: Silagem) {
  editando.value = s;
  form.value = {
    nome: s.nome, tipo: s.tipo, data_ensilagem: s.data_ensilagem ?? "",
    ms_meta: s.ms_meta !== null ? (s.ms_meta * 100).toString() : "",
    ms_real: s.ms_real !== null ? (s.ms_real * 100).toString() : "",
    umidade: s.umidade !== null ? (s.umidade * 100).toString() : "",
    temperatura: s.temperatura?.toString() ?? "",
    quantidade_t: s.quantidade_t?.toString() ?? "",
    consumo_diario_t: s.consumo_diario_t?.toString() ?? "",
    estoque_seguranca_t: s.estoque_seguranca_t?.toString() ?? "",
    maquinario: s.maquinario ?? "", destino: s.destino ?? "",
    responsavel: s.responsavel ?? "", observacao: s.observacao ?? "", situacao: s.situacao,
  };
  erroModal.value = ""; modal.value = true;
}
// o usuário digita 34 (%) e gravamos 0.34
const frac = (v: string) => (v ? parseFloat(v) / 100 : null);
const num = (v: string) => (v ? parseFloat(v) : null);

async function salvar() {
  if (!form.value.nome.trim()) { erroModal.value = "Dê um nome ao silo (ex: Silagem 1)."; return; }
  salvando.value = true; erroModal.value = "";
  const body: any = {
    nome: form.value.nome.trim(), tipo: form.value.tipo,
    data_ensilagem: form.value.data_ensilagem || null,
    ms_meta: frac(form.value.ms_meta), ms_real: frac(form.value.ms_real),
    umidade: frac(form.value.umidade), temperatura: num(form.value.temperatura),
    quantidade_t: num(form.value.quantidade_t), consumo_diario_t: num(form.value.consumo_diario_t),
    estoque_seguranca_t: num(form.value.estoque_seguranca_t),
    maquinario: form.value.maquinario || null, destino: form.value.destino || null,
    responsavel: form.value.responsavel || null, observacao: form.value.observacao || null,
    situacao: form.value.situacao,
  };
  try {
    if (editando.value) await editarSilagem(editando.value.id, body);
    else await criarSilagem(fazendaId.value, body);
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
async function remover(s: Silagem) {
  if (!confirm(`Excluir "${s.nome}"?`)) return;
  try { await excluirSilagem(s.id); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell title="Silagem" sub="Tipos de silo, qualidade e colheita" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Volumoso</div>
      <h1>Silagem</h1>
      <p>Cada silo com seu <b>tipo</b> (milho, capim, sorgo...), a <b>matéria seca</b>, umidade e temperatura, mais os dados da <b>colheita</b> (maquinário usado e para qual curral). O saldo em toneladas continua no Estoque.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="Silos" :value="dados.total_silos" :sub="`${dados.silos_abertos} abertos`" :icon="Layers" tone="primary" />
      <KpiCard label="Total produzido" :value="`${dados.total_t} t`" sub="somando os silos" emoji="🌽" tone="blue" />
      <KpiCard label="Matéria seca média" :value="pct(dados.ms_media)"
               :sub="`alvo ${pct(dados.ms_alvo)}`" :icon="Droplets" :tone="msTone" />
      <KpiCard label="Dias estimados" :value="dados.dias_estimados === null ? '—' : `${dados.dias_estimados} d`"
               :sub="dados.dias_ate_seguranca !== null ? `${dados.dias_ate_seguranca} d até a reserva` : 'pelo consumo informado'"
               :icon="CalendarClock" tone="amber" />
    </div>

    <div v-if="dados?.abaixo_seguranca.length" class="aviso aviso--perigo">
      <PackageMinus :size="18" />
      <span>No estoque de segurança: <b>{{ dados.abaixo_seguranca.join(", ") }}</b> — hora de repor o volumoso.</span>
    </div>

    <div v-if="dados?.fora_do_alvo.length" class="aviso">
      <AlertTriangle :size="18" />
      <span>Fora do alvo de matéria seca: <b>{{ dados.fora_do_alvo.join(", ") }}</b> — risco de perda no silo.</span>
    </div>

    <Panel title="Composição por tipo" sub="toneladas por tipo de silagem" v-if="dados && Object.keys(dados.por_tipo).length">
      <div class="barras">
        <div v-for="(t, tipo) in dados.por_tipo" :key="tipo" class="barra">
          <div class="barra__l"><span>{{ rotTipo(String(tipo)) }}</span><b class="tnum">{{ t }} t</b></div>
          <div class="barra__t"><div class="barra__f" :style="{ width: `${(t / dados.total_t) * 100}%` }" /></div>
        </div>
      </div>
    </Panel>

    <Panel title="Silos" sub="qualidade e dados da colheita" v-if="dados">
      <template #actions>
        <button class="btn btn--primary" style="height:34px" @click="abrirNovo"><Plus :size="15" /> Nova silagem</button>
      </template>
      <div class="tbl-wrap">
        <table class="tbl">
          <thead>
            <tr><th>Silo</th><th>Tipo</th><th>Ensilagem</th><th class="num">Qtd</th><th class="num">MS</th>
                <th class="num">Umidade</th><th class="num">Temp.</th><th>Maquinário</th><th>Destino</th><th class="num">Ações</th></tr>
          </thead>
          <tbody>
            <tr v-for="s in dados.silos" :key="s.id">
              <td>
                <b>{{ s.nome }}</b>
                <span v-if="s.situacao !== 'aberto'" class="badge REVISAR" style="margin-left:6px"><span class="dot" />{{ s.situacao }}</span>
              </td>
              <td>{{ rotTipo(s.tipo) }}</td>
              <td class="muted">{{ fmtData(s.data_ensilagem) }}</td>
              <td class="num tnum" :class="noMinimo(s) ? 'minimo' : ''">
                {{ s.quantidade_t ?? "—" }}
                <PackageMinus v-if="noMinimo(s)" :size="12" />
                <div v-if="s.estoque_seguranca_t !== null" class="muted seg">mín {{ s.estoque_seguranca_t }}</div>
              </td>
              <td class="num tnum" :class="foraDoAlvo(s) ? 'fora' : ''">
                {{ pct(s.ms_real) }}
                <AlertTriangle v-if="foraDoAlvo(s)" :size="12" />
              </td>
              <td class="num tnum">{{ pct(s.umidade) }}</td>
              <td class="num tnum">{{ s.temperatura !== null ? `${s.temperatura}°C` : "—" }}</td>
              <td class="muted">{{ s.maquinario ?? "—" }}</td>
              <td class="muted">{{ s.destino ?? "—" }}</td>
              <td class="num acoes">
                <button class="iconbtn" @click="abrirEdicao(s)"><Pencil :size="14" /></button>
                <button class="iconbtn danger" @click="remover(s)"><Trash2 :size="14" /></button>
              </td>
            </tr>
            <tr v-if="!dados.silos.length"><td colspan="10" class="vazio">Nenhuma silagem cadastrada ainda.</td></tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <Modal v-if="modal" :titulo="editando ? 'Editar silagem' : 'Nova silagem'" sub="tipo, qualidade e colheita" @fechar="modal = false">
      <div class="mform">
        <div class="dupla">
          <div class="field"><label>Nome do silo *</label>
            <input class="input" v-model="form.nome" placeholder="ex: Silagem 1" />
          </div>
          <div class="field"><label>Tipo *</label>
            <select class="input" v-model="form.tipo">
              <option v-for="t in TIPOS_SILAGEM" :key="t.valor" :value="t.valor">{{ t.rotulo }}</option>
            </select>
          </div>
        </div>
        <div class="dupla">
          <div class="field"><label>Data da ensilagem</label>
            <input class="input" type="date" v-model="form.data_ensilagem" />
          </div>
          <div class="field"><label>Situação</label>
            <select class="input" v-model="form.situacao">
              <option value="aberto">Aberto</option>
              <option value="fechado">Fechado (fermentando)</option>
              <option value="consumido">Consumido</option>
            </select>
          </div>
        </div>

        <div class="secao">Qualidade</div>
        <div class="tripla">
          <div class="field"><label>MS meta (%)</label>
            <input class="input tnum" type="number" v-model="form.ms_meta" placeholder="34" />
          </div>
          <div class="field"><label>MS real (%)</label>
            <input class="input tnum" type="number" v-model="form.ms_real" placeholder="32" />
          </div>
          <div class="field"><label>Umidade (%)</label>
            <input class="input tnum" type="number" v-model="form.umidade" placeholder="66" />
          </div>
        </div>
        <div class="dupla">
          <div class="field"><label>Temperatura (°C)</label>
            <input class="input tnum" type="number" v-model="form.temperatura" placeholder="28" />
          </div>
          <div class="field"><label>Quantidade (t)</label>
            <input class="input tnum" type="number" v-model="form.quantidade_t" placeholder="800" />
          </div>
        </div>
        <div class="dupla">
          <div class="field"><label>Consumo diário (t/dia)</label>
            <input class="input tnum" type="number" v-model="form.consumo_diario_t" placeholder="6" />
            <span class="hint">Usado para estimar os dias de silagem.</span>
          </div>
          <div class="field"><label>Estoque de segurança (t)</label>
            <input class="input tnum" type="number" v-model="form.estoque_seguranca_t" placeholder="100" />
            <span class="hint">Quando o silo chegar nesse volume, a tela avisa.</span>
          </div>
        </div>

        <div class="secao">Colheita</div>
        <div class="dupla">
          <div class="field"><label>Maquinário</label>
            <input class="input" v-model="form.maquinario" placeholder="ex: Colhedora JD + 2 tratores" />
          </div>
          <div class="field"><label>Destino</label>
            <input class="input" v-model="form.destino" placeholder="ex: Curral 1 / Confinamento" />
          </div>
        </div>
        <div class="dupla">
          <div class="field"><label>Responsável</label>
            <input class="input" v-model="form.responsavel" />
          </div>
          <div class="field"><label>Observação</label>
            <input class="input" v-model="form.observacao" />
          </div>
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
.aviso { display: flex; align-items: center; gap: 10px; background: #fff8ef; border: 1px solid #f0dcc0;
  color: #8a5a12; border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; font-size: 14px; }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 940px; border-collapse: collapse; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.fora { color: var(--amber); font-weight: 700; }
.minimo { color: var(--danger); font-weight: 700; }
.seg { font-size: 11px; font-weight: 400; margin-top: 2px; }
.aviso--perigo { background: #fcebeb; border-color: #f0c9c9; color: #8a1212; }
.acoes { white-space: nowrap; display: flex; gap: 4px; justify-content: flex-end; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn:hover { color: var(--primary); border-color: var(--primary); }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.barras { display: flex; flex-direction: column; gap: 10px; }
.barra__l { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
.barra__t { height: 8px; background: var(--bg); border-radius: 999px; overflow: hidden; }
.barra__f { height: 100%; background: var(--primary); border-radius: 999px; }
.mform { display: flex; flex-direction: column; gap: 14px; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
.mform .hint { font-size: 12px; color: var(--muted); }
.dupla { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.tripla { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.secao { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted);
  font-weight: 700; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
@media (max-width: 700px) { .dupla, .tripla { grid-template-columns: 1fr; } }
</style>
