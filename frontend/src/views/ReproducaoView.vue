<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { TrendingUp, CircleCheck, TriangleAlert, Plus, Trash2 } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getAnimais, getReproducao, criarInseminacao, registrarDG, excluirInseminacao,
  type Fazenda, type Animal, type ResumoReproducao,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const dados = ref<ResumoReproducao | null>(null);
const matrizes = ref<Animal[]>([]);
const erro = ref("");
const META = 0.82;

const fmtPct = (v: number | null) => (v === null ? "—" : (v * 100).toFixed(0) + "%");
const fmtData = (d: string) => d.split("-").reverse().join("/");
const badge = (r: string) => (r === "prenhe" ? "OK" : r === "vazia" ? "ALERTA" : "REVISAR");
const rotulo = (r: string) => (r === "prenhe" ? "Prenhe" : r === "vazia" ? "Vazia" : "Pendente");

const taxaTone = computed(() => {
  const t = dados.value?.taxa_prenhez;
  if (t === null || t === undefined) return "blue";
  return t >= META ? "primary" : "amber";
});
const maxTouro = computed(() => Math.max(1, ...(dados.value?.por_touro ?? []).map((g) => g.total)));

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try {
    [dados.value, matrizes.value] = await Promise.all([
      getReproducao(fazendaId.value),
      getAnimais(fazendaId.value),
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

// fêmeas (matrizes/novilhas) para o seletor
const femeas = computed(() => matrizes.value.filter((a) => a.sexo === "F"));

// modal nova inseminação
const modal = ref(false);
const form = ref({ animal_id: "", touro: "", inseminador: "", protocolo: "IATF" });
const erroModal = ref("");
const salvando = ref(false);
function abrir() {
  form.value = { animal_id: "", touro: "", inseminador: "", protocolo: "IATF" };
  erroModal.value = ""; modal.value = true;
}
async function salvar() {
  if (!form.value.animal_id) { erroModal.value = "Escolha a matriz."; return; }
  if (!form.value.touro.trim()) { erroModal.value = "Informe o touro/sêmen."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    await criarInseminacao(fazendaId.value, {
      animal_id: form.value.animal_id, touro: form.value.touro,
      inseminador: form.value.inseminador || undefined, protocolo: form.value.protocolo || undefined,
    });
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}

async function dg(insId: string, resultado: "prenhe" | "vazia") {
  try { await registrarDG(insId, resultado); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function remover(insId: string) {
  if (!confirm("Excluir esta inseminação?")) return;
  try { await excluirInseminacao(insId); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell title="Reprodução" sub="IATF e prenhez" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Módulo da cria</div>
      <h1>Reprodução · IATF e prenhez</h1>
      <p>Registre a inseminação (matriz, touro, inseminador) e depois o diagnóstico de gestação. O sistema calcula a taxa de prenhez sozinho — inclusive <b>por touro</b>, pra você saber o que está funcionando.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="Inseminadas" :value="dados.total" sub="matrizes" emoji="🧬" tone="blue" />
      <KpiCard label="Taxa de prenhez" :value="fmtPct(dados.taxa_prenhez)" :sub="`meta ${fmtPct(META)}`"
               :icon="TrendingUp" :tone="taxaTone" />
      <KpiCard label="Prenhes" :value="dados.prenhes" sub="confirmadas" :icon="CircleCheck" tone="primary" />
      <KpiCard label="Vazias / pendentes" :value="`${dados.vazias} / ${dados.pendentes}`"
               sub="revisar / aguardando DG" :icon="TriangleAlert" tone="amber" />
    </div>

    <div class="grid2" v-if="dados">
      <Panel title="Inseminações" sub="registre o DG nas pendentes">
        <template #actions>
          <button class="btn btn--primary" style="height:34px" @click="abrir"><Plus :size="15" /> Nova inseminação</button>
        </template>
        <div class="tbl-wrap">
          <table class="tbl">
            <colgroup><col style="width:16%"/><col style="width:22%"/><col style="width:20%"/><col style="width:12%"/><col style="width:30%"/></colgroup>
            <thead><tr><th>Matriz</th><th>Touro/sêmen</th><th>Inseminador</th><th>Data</th><th>DG</th></tr></thead>
            <tbody>
              <tr v-for="i in dados.inseminacoes" :key="i.id">
                <td><strong>{{ i.animal_brinco }}</strong></td>
                <td>{{ i.touro }}</td>
                <td class="muted">{{ i.inseminador ?? "—" }}</td>
                <td class="muted">{{ fmtData(i.data) }}</td>
                <td>
                  <div v-if="i.resultado === 'pendente'" class="row" style="gap:6px">
                    <button class="mini ok" @click="dg(i.id, 'prenhe')">Prenhe</button>
                    <button class="mini bad" @click="dg(i.id, 'vazia')">Vazia</button>
                    <button class="iconbtn danger" title="Excluir" @click="remover(i.id)"><Trash2 :size="14" /></button>
                  </div>
                  <div v-else class="row" style="gap:8px">
                    <span :class="['badge', badge(i.resultado)]"><span class="dot" /> {{ rotulo(i.resultado) }}</span>
                    <button class="iconbtn danger" title="Excluir" @click="remover(i.id)"><Trash2 :size="14" /></button>
                  </div>
                </td>
              </tr>
              <tr v-if="!dados.inseminacoes.length"><td colspan="5" class="vazio">Nenhuma inseminação. Clique em "Nova inseminação".</td></tr>
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Prenhez por touro" sub="calculado dos DGs">
        <div v-if="dados.por_touro.length" style="padding:4px 0">
          <div class="bar-row" v-for="g in dados.por_touro" :key="g.nome">
            <span class="bl">{{ g.nome }}</span>
            <div class="bar"><span :style="{ width: (g.total / maxTouro * 100) + '%', background: g.taxa === null ? '#9db2bd' : (g.taxa >= META ? 'var(--primary)' : (g.taxa >= 0.5 ? 'var(--amber)' : 'var(--danger)')) }" /></div>
            <b class="bv tnum">{{ g.taxa === null ? "—" : fmtPct(g.taxa) }}</b>
          </div>
          <div class="nota">📌 A média esconde diferenças. Aqui você vê qual touro está puxando a prenhez pra baixo — decisão de compra de sêmen que a planilha não dá.</div>
        </div>
        <div v-else class="muted" style="padding:10px">Sem dados ainda.</div>
      </Panel>
    </div>

    <Modal v-if="modal" titulo="Nova inseminação" sub="IATF de uma matriz" @fechar="modal = false">
      <div class="mform">
        <div class="field"><label>Matriz *</label>
          <select class="input selc" v-model="form.animal_id">
            <option value="">— escolha a matriz —</option>
            <option v-for="a in femeas" :key="a.id" :value="a.id">{{ a.brinco }} · {{ a.categoria }} {{ a.raca }}</option>
          </select>
          <span class="hint">Vaca/novilha que foi inseminada.</span>
        </div>
        <div class="field"><label>Touro / sêmen *</label>
          <input class="input" v-model="form.touro" placeholder="ex: Angus FP" />
          <span class="hint">Qual touro ou sêmen foi usado (o "pai").</span>
        </div>
        <div class="two">
          <div class="field"><label>Inseminador</label>
            <input class="input" v-model="form.inseminador" placeholder="ex: Vet. Rocha" />
          </div>
          <div class="field"><label>Protocolo</label>
            <input class="input" v-model="form.protocolo" placeholder="IATF" />
          </div>
        </div>
        <p v-if="erroModal" class="error">{{ erroModal }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modal = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvando" @click="salvar">Registrar inseminação</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.selc { width: auto; min-width: 240px; appearance: auto; }
.grid2 { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; align-items: start; }
@media (max-width: 900px) { .grid2 { grid-template-columns: 1fr; } }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 520px; border-collapse: collapse; table-layout: fixed; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.mini { height: 28px; padding: 0 10px; border-radius: 6px; font-size: 12.5px; font-weight: 700; cursor: pointer; border: 1px solid; }
.mini.ok { background: #e7f4ee; color: #0b7a52; border-color: #cfe6da; }
.mini.ok:hover { background: #d7ecdf; }
.mini.bad { background: #fcebeb; color: #b91c1c; border-color: #f0c9c9; }
.mini.bad:hover { background: #f8dcdc; }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.bar-row { display: grid; grid-template-columns: 110px 1fr 46px; align-items: center; gap: 10px; padding: 8px 0; }
.bl { font-size: 13.5px; }
.bar { height: 10px; border-radius: 6px; background: #eef2f4; overflow: hidden; }
.bar > span { display: block; height: 100%; border-radius: 6px; }
.bv { font-size: 13px; text-align: right; }
.nota { background: #f2f8f5; border: 1px solid #cfe6da; border-radius: 8px; padding: 11px 13px; font-size: 12.5px; color: #245c47; margin-top: 12px; }
.mform { display: flex; flex-direction: column; gap: 14px; }
.mform .two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
.mform .hint { font-size: 12px; color: var(--muted); }
</style>
