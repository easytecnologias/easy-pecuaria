<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Gauge, Scale, TrendingDown, TrendingUp, Plus, Trash2 } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getAnimais, getEscore, registrarEscore, excluirEscore,
  type Fazenda, type Animal, type ResumoEscore,
} from "../api";

const ESCORES = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5];
const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const animais = ref<Animal[]>([]);
const dados = ref<ResumoEscore | null>(null);
const erro = ref("");

const fmtData = (d: string) => d.split("-").reverse().join("/");
const fmtPct = (v: number | null) => (v === null ? "—" : `${(v * 100).toFixed(0)}%`);
function faixa(e: number) {
  if (e < 2.5) return { rotulo: "Magra", cls: "ALERTA" };
  if (e > 3.5) return { rotulo: "Gorda", cls: "REVISAR" };
  return { rotulo: "Ideal", cls: "OK" };
}
const total = computed(() => dados.value?.n_avaliados ?? 0);
function larg(n: number) { return total.value ? (n / total.value) * 100 : 0; }

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try {
    [dados.value, animais.value] = await Promise.all([
      getEscore(fazendaId.value), getAnimais(fazendaId.value),
    ]);
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  if (fazendas.value[0]) { fazendaId.value = fazendas.value[0].id; await carregar(); }
}
watch(fazendaId, carregar);
onMounted(init);

const ativos = computed(() => animais.value.filter((a) => a.status === "ativo"));

const modal = ref(false);
const form = ref({ animal_id: "", escore: "3", data: "", observacao: "" });
const erroModal = ref("");
const salvando = ref(false);
function abrir() {
  form.value = { animal_id: "", escore: "3", data: "", observacao: "" };
  erroModal.value = ""; modal.value = true;
}
async function salvar() {
  if (!form.value.animal_id) { erroModal.value = "Escolha o animal."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    await registrarEscore(fazendaId.value, {
      animal_id: form.value.animal_id, escore: parseFloat(form.value.escore),
      data: form.value.data || undefined, observacao: form.value.observacao || undefined,
    });
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
async function remover(id: string) {
  if (!confirm("Excluir esta avaliação de escore?")) return;
  try { await excluirEscore(id); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell title="Escore corporal" sub="Condição corporal (ECC)" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Nutrição & reprodução</div>
      <h1>Escore de condição corporal</h1>
      <p>Avalie a gordura de reserva na escala <b>1 a 5</b>. A matriz precisa chegar na monta e no parto no escore <b>ideal (2,5–3,5)</b>: magra emprenha menos, gorda tem parto difícil. Veja a distribuição do rebanho e aja no manejo.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="Avaliados" :value="dados.n_avaliados" sub="animais com ECC" :icon="Scale" tone="blue" />
      <KpiCard label="Escore médio" :value="dados.media === null ? '—' : dados.media.toFixed(1)" sub="escala 1–5" :icon="Gauge" tone="primary" />
      <KpiCard label="No ideal" :value="fmtPct(dados.pct_ideais)" :sub="`${dados.ideais} de ${dados.n_avaliados}`" :icon="TrendingUp"
               :tone="(dados.pct_ideais ?? 1) >= 0.7 ? 'primary' : 'amber'" />
      <KpiCard label="Magras" :value="dados.magras" sub="ECC < 2,5" :icon="TrendingDown" :tone="dados.magras ? 'danger' : 'primary'" />
    </div>

    <Panel title="Distribuição do rebanho" sub="por faixa de escore (última avaliação)" v-if="dados && dados.n_avaliados">
      <div class="dist">
        <div class="dist-bar">
          <div class="seg magra" :style="{ width: `${larg(dados.magras)}%` }" :title="`Magras: ${dados.magras}`" />
          <div class="seg ideal" :style="{ width: `${larg(dados.ideais)}%` }" :title="`Ideais: ${dados.ideais}`" />
          <div class="seg gorda" :style="{ width: `${larg(dados.gordas)}%` }" :title="`Gordas: ${dados.gordas}`" />
        </div>
        <div class="dist-leg">
          <span><i class="dot magra" /> Magras (&lt;2,5): <b>{{ dados.magras }}</b></span>
          <span><i class="dot ideal" /> Ideais (2,5–3,5): <b>{{ dados.ideais }}</b></span>
          <span><i class="dot gorda" /> Gordas (&gt;3,5): <b>{{ dados.gordas }}</b></span>
        </div>
      </div>
    </Panel>

    <Panel title="Avaliações" sub="mais recentes primeiro" v-if="dados">
      <template #actions>
        <button class="btn btn--primary" style="height:34px" @click="abrir"><Plus :size="15" /> Avaliar escore</button>
      </template>
      <div class="tbl-wrap">
        <table class="tbl">
          <colgroup><col style="width:14%"/><col style="width:16%"/><col style="width:18%"/><col style="width:14%"/><col style="width:26%"/><col style="width:12%"/></colgroup>
          <thead><tr><th>Data</th><th>Brinco</th><th>Categoria</th><th class="num">Escore</th><th>Faixa</th><th class="num">Ações</th></tr></thead>
          <tbody>
            <tr v-for="h in dados.historico" :key="h.id">
              <td>{{ fmtData(h.data) }}</td>
              <td>
                <RouterLink :to="`/animais/${h.animal_id}`" class="link">{{ h.brinco }}</RouterLink>
              </td>
              <td class="muted">{{ h.categoria ?? "—" }}</td>
              <td class="num tnum"><strong>{{ h.escore.toFixed(1) }}</strong></td>
              <td><span :class="['badge', faixa(h.escore).cls]"><span class="dot" /> {{ faixa(h.escore).rotulo }}</span></td>
              <td class="num"><button class="iconbtn danger" @click="remover(h.id)"><Trash2 :size="14" /></button></td>
            </tr>
            <tr v-if="!dados.historico.length"><td colspan="6" class="vazio">Nenhuma avaliação ainda.</td></tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <Modal v-if="modal" titulo="Avaliar escore corporal" sub="condição corporal na escala 1–5" :largura="520" @fechar="modal = false">
      <div class="mform">
        <div class="field"><label>Animal *</label>
          <select class="input selc" v-model="form.animal_id">
            <option value="">— escolha —</option>
            <option v-for="a in ativos" :key="a.id" :value="a.id">{{ a.brinco }} · {{ a.categoria }}</option>
          </select>
        </div>
        <div class="two">
          <div class="field"><label>Escore (1–5)</label>
            <select class="input selc" v-model="form.escore">
              <option v-for="e in ESCORES" :key="e" :value="String(e)">{{ e.toFixed(1) }} — {{ faixa(e).rotulo }}</option>
            </select>
          </div>
          <div class="field"><label>Data</label><input class="input" type="date" v-model="form.data" /></div>
        </div>
        <div class="field"><label>Observação</label><input class="input" v-model="form.observacao" placeholder="ex: pós-parto, lote de recria" /></div>
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
.dist { display: flex; flex-direction: column; gap: 12px; }
.dist-bar { display: flex; height: 22px; border-radius: 6px; overflow: hidden; background: #eef2f4; }
.dist-bar .seg { height: 100%; }
.dist-bar .seg.magra { background: var(--danger); }
.dist-bar .seg.ideal { background: var(--primary); }
.dist-bar .seg.gorda { background: #d99a2b; }
.dist-leg { display: flex; gap: 20px; flex-wrap: wrap; font-size: 13px; color: var(--muted); }
.dist-leg b { color: var(--text); }
.dist-leg .dot, .mform i.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; vertical-align: baseline; }
.dot.magra { background: var(--danger); }
.dot.ideal { background: var(--primary); }
.dot.gorda { background: #d99a2b; }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 560px; border-collapse: collapse; table-layout: fixed; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.link { color: var(--primary); font-weight: 600; text-decoration: none; }
.link:hover { text-decoration: underline; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.mform { display: flex; flex-direction: column; gap: 13px; }
.mform .two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
</style>
