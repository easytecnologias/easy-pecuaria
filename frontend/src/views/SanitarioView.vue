<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { CalendarClock, Plus, Trash2 } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getLotes, getAnimais, getSanitario, registrarAplicacao, excluirEventoSanitario,
  type Fazenda, type Lote, type Animal, type ResumoSanitario,
} from "../api";

const TIPOS = ["vacina", "vermifugo", "tratamento", "exame", "carrapaticida", "hormonio"];
const rotuloTipo: Record<string, string> = { vacina: "Vacina", vermifugo: "Vermífugo", tratamento: "Tratamento", exame: "Exame", carrapaticida: "Carrapaticida", hormonio: "Hormônio" };

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const lotes = ref<Lote[]>([]);
const animais = ref<Animal[]>([]);
const dados = ref<ResumoSanitario | null>(null);
const erro = ref("");
const fmtData = (d: string) => d.split("-").reverse().join("/");

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try {
    [dados.value, lotes.value, animais.value] = await Promise.all([
      getSanitario(fazendaId.value), getLotes(fazendaId.value), getAnimais(fazendaId.value),
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

const modal = ref(false);
const form = ref({ alvo: "lote", lote_id: "", animal_id: "", tipo: "vacina", produto: "", data: "", proxima_aplicacao: "", dose: "", observacao: "" });
const erroModal = ref("");
const salvando = ref(false);
function abrir() {
  form.value = { alvo: "lote", lote_id: lotes.value[0]?.id ?? "", animal_id: "", tipo: "vacina", produto: "", data: "", proxima_aplicacao: "", dose: "", observacao: "" };
  erroModal.value = ""; modal.value = true;
}
async function salvar() {
  if (!form.value.produto.trim()) { erroModal.value = "Informe o produto."; return; }
  if (form.value.alvo === "lote" && !form.value.lote_id) { erroModal.value = "Escolha o lote."; return; }
  if (form.value.alvo === "animal" && !form.value.animal_id) { erroModal.value = "Escolha o animal."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    await registrarAplicacao(fazendaId.value, {
      tipo: form.value.tipo, produto: form.value.produto,
      data: form.value.data || undefined, proxima_aplicacao: form.value.proxima_aplicacao || null,
      dose: form.value.dose || undefined, observacao: form.value.observacao || undefined,
      lote_id: form.value.alvo === "lote" ? form.value.lote_id : null,
      animal_id: form.value.alvo === "animal" ? form.value.animal_id : null,
    });
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
async function remover(id: string) {
  if (!confirm("Excluir este registro sanitário?")) return;
  try { await excluirEventoSanitario(id); await carregar(); } catch (e) { erro.value = String(e); }
}
</script>

<template>
  <AppShell title="Sanitário" sub="Vacinas, vermífugos e tratamentos" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Saúde do rebanho</div>
      <h1>Controle sanitário</h1>
      <p>Registre vacinas, vermífugos e tratamentos — num animal ou no <b>lote inteiro</b>. Informe a <b>próxima aplicação</b> e o sistema monta o calendário e avisa o que está vencendo.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId"><option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option></select>
    </div>
    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="Aplicações registradas" :value="dados.total" sub="no histórico" emoji="💉" tone="blue" />
      <KpiCard label="Vencendo" :value="dados.vencendo" sub="próx. 15 dias" :icon="CalendarClock" :tone="dados.vencendo ? 'danger' : 'primary'" />
    </div>

    <div class="grid2" v-if="dados">
      <Panel title="Agenda — próximas aplicações" sub="por produto e data">
        <template #actions>
          <button class="btn btn--primary" style="height:34px" @click="abrir"><Plus :size="15" /> Registrar aplicação</button>
        </template>
        <div class="tbl-wrap">
          <table class="tbl">
            <colgroup><col style="width:32%"/><col style="width:22%"/><col style="width:20%"/><col style="width:26%"/></colgroup>
            <thead><tr><th>Produto</th><th>Tipo</th><th class="num">Animais</th><th class="num">Próxima</th></tr></thead>
            <tbody>
              <tr v-for="(a,i) in dados.agenda" :key="i">
                <td><strong>{{ a.produto }}</strong></td>
                <td class="muted">{{ rotuloTipo[a.tipo] ?? a.tipo }}</td>
                <td class="num tnum">{{ a.animais }}</td>
                <td class="num">
                  <span :class="['badge', a.vencido ? 'ALERTA' : a.vence_proximo ? 'REVISAR' : 'OK']"><span class="dot"/> {{ fmtData(a.proxima) }}</span>
                </td>
              </tr>
              <tr v-if="!dados.agenda.length"><td colspan="4" class="vazio">Nenhuma aplicação agendada.</td></tr>
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Histórico" sub="aplicações recentes">
        <div class="tbl-wrap">
          <table class="tbl">
            <colgroup><col style="width:22%"/><col style="width:32%"/><col style="width:22%"/><col style="width:12%"/><col style="width:12%"/></colgroup>
            <thead><tr><th>Brinco</th><th>Produto</th><th>Tipo</th><th class="num">Data</th><th class="num"></th></tr></thead>
            <tbody>
              <tr v-for="h in dados.historico" :key="h.id">
                <td><strong>{{ h.brinco }}</strong></td>
                <td>{{ h.produto }}</td>
                <td class="muted">{{ rotuloTipo[h.tipo] ?? h.tipo }}</td>
                <td class="num muted">{{ fmtData(h.data) }}</td>
                <td class="num"><button class="iconbtn danger" @click="remover(h.id)"><Trash2 :size="13"/></button></td>
              </tr>
              <tr v-if="!dados.historico.length"><td colspan="5" class="vazio">Sem registros.</td></tr>
            </tbody>
          </table>
        </div>
      </Panel>
    </div>

    <Modal v-if="modal" titulo="Registrar aplicação" sub="vacina, vermífugo ou tratamento" :largura="560" @fechar="modal = false">
      <div class="mform">
        <div class="field"><label>Aplicar em</label>
          <div class="row" style="gap:16px">
            <label class="opt"><input type="radio" value="lote" v-model="form.alvo" /> Lote inteiro</label>
            <label class="opt"><input type="radio" value="animal" v-model="form.alvo" /> Um animal</label>
          </div>
        </div>
        <div class="field" v-if="form.alvo === 'lote'"><label>Lote</label>
          <select class="input selc" v-model="form.lote_id"><option v-for="l in lotes" :key="l.id" :value="l.id">{{ l.nome }} ({{ l.n_animais }})</option></select>
        </div>
        <div class="field" v-else><label>Animal</label>
          <select class="input selc" v-model="form.animal_id"><option value="">— escolha —</option><option v-for="a in animais" :key="a.id" :value="a.id">{{ a.brinco }} · {{ a.categoria }}</option></select>
        </div>
        <div class="two">
          <div class="field"><label>Tipo</label>
            <select class="input selc" v-model="form.tipo"><option v-for="t in TIPOS" :key="t" :value="t">{{ rotuloTipo[t] }}</option></select>
          </div>
          <div class="field"><label>Produto *</label><input class="input" v-model="form.produto" placeholder="ex: Aftosa, Ivermectina" /></div>
        </div>
        <div class="two">
          <div class="field"><label>Data</label><input class="input" type="date" v-model="form.data" /></div>
          <div class="field"><label>Próxima aplicação</label><input class="input" type="date" v-model="form.proxima_aplicacao" /></div>
        </div>
        <div class="two">
          <div class="field"><label>Dose</label><input class="input" v-model="form.dose" placeholder="ex: 5 ml" /></div>
          <div class="field"><label>Observação</label><input class="input" v-model="form.observacao" /></div>
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
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }
@media (max-width: 900px) { .grid2 { grid-template-columns: 1fr; } }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 440px; border-collapse: collapse; table-layout: fixed; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.vazio { text-align: center; padding: 18px; color: var(--muted); }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted); width: 26px; height: 26px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.mform { display: flex; flex-direction: column; gap: 13px; }
.mform .two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
.opt { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 500; }
</style>
