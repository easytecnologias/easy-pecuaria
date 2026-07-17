<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Baby, HeartPulse, HeartCrack, Percent, Plus, Trash2 } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getAnimais, getPartos, registrarParto, excluirParto,
  type Fazenda, type Animal, type ResumoPartos,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const animais = ref<Animal[]>([]);
const dados = ref<ResumoPartos | null>(null);
const erro = ref("");

const fmtData = (d: string) => d.split("-").reverse().join("/");
const fmtPct = (v: number | null) => (v === null ? "—" : `${(v * 100).toFixed(1)}%`);
// mães possíveis: fêmeas ativas (matrizes e novilhas)
const matrizes = computed(() =>
  animais.value.filter((a) => a.sexo === "F" && a.status === "ativo")
);

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try {
    [dados.value, animais.value] = await Promise.all([
      getPartos(fazendaId.value), getAnimais(fazendaId.value),
    ]);
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  if (fazendas.value[0]) { fazendaId.value = fazendas.value[0].id; await carregar(); }
}
watch(fazendaId, (_v, old) => { if (old) carregar(); });
onMounted(init);

const modal = ref(false);
const form = ref({ mae_id: "", data: "", resultado: "nascido_vivo" as "nascido_vivo" | "natimorto",
  sexo_bezerro: "F", brinco_bezerro: "", peso_nascimento: "", observacao: "" });
const erroModal = ref("");
const salvando = ref(false);
function abrir() {
  form.value = { mae_id: "", data: "", resultado: "nascido_vivo", sexo_bezerro: "F",
    brinco_bezerro: "", peso_nascimento: "", observacao: "" };
  erroModal.value = ""; modal.value = true;
}
async function salvar() {
  if (!form.value.mae_id) { erroModal.value = "Escolha a mãe."; return; }
  if (form.value.resultado === "nascido_vivo" && !form.value.brinco_bezerro.trim()) {
    erroModal.value = "Informe o brinco do bezerro."; return;
  }
  const peso = form.value.peso_nascimento ? parseFloat(form.value.peso_nascimento.replace(",", ".")) : undefined;
  salvando.value = true; erroModal.value = "";
  try {
    await registrarParto(fazendaId.value, {
      mae_id: form.value.mae_id, data: form.value.data || undefined,
      resultado: form.value.resultado,
      sexo_bezerro: form.value.resultado === "nascido_vivo" ? form.value.sexo_bezerro : undefined,
      brinco_bezerro: form.value.resultado === "nascido_vivo" ? form.value.brinco_bezerro.trim() : undefined,
      peso_nascimento: peso, observacao: form.value.observacao || undefined,
    });
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
async function remover(p: { id: string; brinco_bezerro: string | null }) {
  const aviso = p.brinco_bezerro
    ? `Excluir este parto? O bezerro ${p.brinco_bezerro} também será removido do rebanho.`
    : "Excluir este parto?";
  if (!confirm(aviso)) return;
  try { await excluirParto(p.id); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell title="Partos" sub="Nascimentos e natalidade" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Cria</div>
      <h1>Partos e nascimentos</h1>
      <p>Registre o parto de cada matriz. Quando nasce vivo, o <b>bezerro entra automaticamente no rebanho</b> ligado à mãe — e aparece na evolução do rebanho. A natalidade abastece o acompanhamento reprodutivo.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="Partos (12 meses)" :value="dados.partos_12m" sub="no período" :icon="Baby" tone="blue" />
      <KpiCard label="Nascidos vivos" :value="dados.vivos_12m" sub="últimos 12 meses" :icon="HeartPulse" tone="primary" />
      <KpiCard label="Natimortos" :value="dados.natimortos_12m"
               :sub="`natimort. ${fmtPct(dados.taxa_natimortalidade)}`" :icon="HeartCrack"
               :tone="dados.natimortos_12m ? 'danger' : 'primary'" />
      <KpiCard label="Taxa de natalidade" :value="fmtPct(dados.taxa_natalidade)"
               :sub="`${dados.matrizes} matrizes`" :icon="Percent" tone="amber" />
    </div>

    <Panel title="Partos registrados" sub="mais recentes primeiro" v-if="dados">
      <template #actions>
        <button class="btn btn--primary" style="height:34px" @click="abrir"><Plus :size="15" /> Registrar parto</button>
      </template>
      <div class="tbl-wrap">
        <table class="tbl">
          <colgroup><col style="width:14%"/><col style="width:16%"/><col style="width:18%"/><col style="width:12%"/><col style="width:14%"/><col style="width:14%"/><col style="width:12%"/></colgroup>
          <thead><tr><th>Data</th><th>Mãe</th><th>Bezerro</th><th>Sexo</th><th class="num">Peso nasc.</th><th>Resultado</th><th class="num">Ações</th></tr></thead>
          <tbody>
            <tr v-for="p in dados.partos" :key="p.id">
              <td>{{ fmtData(p.data) }}</td>
              <td><strong>{{ p.mae_brinco }}</strong></td>
              <td>
                <RouterLink v-if="p.bezerro_id" :to="`/animais/${p.bezerro_id}`" class="link">{{ p.brinco_bezerro }}</RouterLink>
                <span v-else class="muted">—</span>
              </td>
              <td>{{ p.sexo_bezerro ?? "—" }}</td>
              <td class="num tnum">{{ p.peso_nascimento !== null ? `${p.peso_nascimento} kg` : "—" }}</td>
              <td>
                <span :class="['badge', p.resultado === 'nascido_vivo' ? 'OK' : 'ALERTA']">
                  <span class="dot" /> {{ p.resultado === 'nascido_vivo' ? 'Nascido vivo' : 'Natimorto' }}
                </span>
              </td>
              <td class="num"><button class="iconbtn danger" @click="remover(p)"><Trash2 :size="14" /></button></td>
            </tr>
            <tr v-if="!dados.partos.length"><td colspan="7" class="vazio">Nenhum parto registrado ainda.</td></tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <Modal v-if="modal" titulo="Registrar parto" sub="nascimento de uma matriz" :largura="560" @fechar="modal = false">
      <div class="mform">
        <div class="two">
          <div class="field"><label>Mãe (matriz) *</label>
            <select class="input selc" v-model="form.mae_id">
              <option value="">— escolha —</option>
              <option v-for="m in matrizes" :key="m.id" :value="m.id">{{ m.brinco }} · {{ m.categoria }}</option>
            </select>
          </div>
          <div class="field"><label>Data do parto</label><input class="input" type="date" v-model="form.data" /></div>
        </div>
        <div class="field"><label>Resultado</label>
          <div class="row" style="gap:16px">
            <label class="opt"><input type="radio" value="nascido_vivo" v-model="form.resultado" /> Nascido vivo</label>
            <label class="opt"><input type="radio" value="natimorto" v-model="form.resultado" /> Natimorto</label>
          </div>
        </div>
        <template v-if="form.resultado === 'nascido_vivo'">
          <div class="two">
            <div class="field"><label>Sexo do bezerro</label>
              <select class="input selc" v-model="form.sexo_bezerro">
                <option value="F">Fêmea</option>
                <option value="M">Macho</option>
              </select>
            </div>
            <div class="field"><label>Brinco do bezerro *</label>
              <input class="input" v-model="form.brinco_bezerro" placeholder="ex: B512" />
            </div>
          </div>
        </template>
        <div class="two">
          <div class="field"><label>Peso ao nascer (kg)</label>
            <input class="input tnum" v-model="form.peso_nascimento" placeholder="ex: 32" />
          </div>
          <div class="field"><label>Observação</label><input class="input" v-model="form.observacao" /></div>
        </div>
        <p class="hint" v-if="form.resultado === 'nascido_vivo'">O bezerro será criado no rebanho, no mesmo lote da mãe, já com a genealogia ligada.</p>
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
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 640px; border-collapse: collapse; table-layout: fixed; }
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
.opt { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 500; }
.hint { font-size: 12px; color: var(--muted); }
</style>
