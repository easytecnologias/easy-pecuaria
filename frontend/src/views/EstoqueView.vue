<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Wheat, CalendarClock, TrendingDown, ArrowDownToLine, ArrowUpFromLine, Trash2 } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getEstoque, criarMovimento, excluirMovimento,
  type Fazenda, type ResumoEstoque,
} from "../api";

const SEGURANCA = 45;
const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const dados = ref<ResumoEstoque | null>(null);
const erro = ref("");

const fmtData = (d: string) => d.split("-").reverse().join("/");
const diasTone = computed(() => {
  const d = dados.value?.dias;
  if (d === null || d === undefined) return "blue";
  return d >= SEGURANCA ? "primary" : d >= SEGURANCA * 0.6 ? "amber" : "danger";
});

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try { dados.value = await getEstoque(fazendaId.value); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  const sede = fazendas.value.find((f) => f.nome.includes("Sede")) ?? fazendas.value[0];
  if (sede) { fazendaId.value = sede.id; await carregar(); }
}
watch(fazendaId, (_v, old) => { if (old) carregar(); });
onMounted(init);

const modal = ref(false);
const form = ref({ tipo: "entrada" as "entrada" | "saida", quantidade_t: "", descricao: "" });
const erroModal = ref("");
const salvando = ref(false);
function abrir(tipo: "entrada" | "saida") {
  form.value = { tipo, quantidade_t: "", descricao: "" };
  erroModal.value = ""; modal.value = true;
}
async function salvar() {
  const q = parseFloat(form.value.quantidade_t);
  if (isNaN(q) || q <= 0) { erroModal.value = "Informe a quantidade em toneladas."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    await criarMovimento(fazendaId.value, { tipo: form.value.tipo, quantidade_t: q, descricao: form.value.descricao || undefined });
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
async function remover(id: string) {
  if (!confirm("Excluir este movimento?")) return;
  try { await excluirMovimento(id); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell title="Estoque de volumoso" sub="Silagem e dias de estoque" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Volumoso</div>
      <h1>Estoque de silagem</h1>
      <p>Lance as <b>entradas</b> (ensilagem/compra) e as <b>saídas</b> (consumo do cocho). O sistema calcula o saldo e os <b>dias de estoque</b> — se cair abaixo da segurança ({{ SEGURANCA }} dias), vira alerta.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="Saldo em estoque" :value="`${dados.saldo_t} t`" sub="volumoso disponível" emoji="🌽" tone="primary" />
      <KpiCard label="Dias de estoque" :value="dados.dias === null ? '—' : `${dados.dias} d`"
               :sub="`segurança ${SEGURANCA} d`" :icon="CalendarClock" :tone="diasTone" />
      <KpiCard label="Consumo médio" :value="dados.consumo_diario_t === null ? '—' : `${dados.consumo_diario_t} t/dia`"
               sub="últimos 30 dias" :icon="TrendingDown" tone="blue" />
      <KpiCard label="Movimentos" :value="dados.movimentos.length" sub="registrados" :icon="Wheat" tone="amber" />
    </div>

    <Panel title="Movimentos" sub="entradas e saídas de volumoso" v-if="dados">
      <template #actions>
        <div class="row" style="gap:8px">
          <button class="btn btn--secondary" style="height:34px" @click="abrir('entrada')"><ArrowDownToLine :size="15" /> Entrada</button>
          <button class="btn btn--primary" style="height:34px" @click="abrir('saida')"><ArrowUpFromLine :size="15" /> Saída</button>
        </div>
      </template>
      <div class="tbl-wrap">
        <table class="tbl">
          <colgroup><col style="width:16%"/><col style="width:18%"/><col style="width:18%"/><col style="width:34%"/><col style="width:14%"/></colgroup>
          <thead><tr><th>Data</th><th>Tipo</th><th class="num">Toneladas</th><th>Descrição</th><th class="num">Ações</th></tr></thead>
          <tbody>
            <tr v-for="m in dados.movimentos" :key="m.id">
              <td>{{ fmtData(m.data) }}</td>
              <td>
                <span :class="['badge', m.tipo === 'entrada' ? 'OK' : 'REVISAR']">
                  <span class="dot" /> {{ m.tipo === 'entrada' ? 'Entrada' : 'Saída' }}
                </span>
              </td>
              <td class="num tnum">{{ m.quantidade_t }} t</td>
              <td class="muted">{{ m.descricao ?? "—" }}</td>
              <td class="num"><button class="iconbtn danger" @click="remover(m.id)"><Trash2 :size="14" /></button></td>
            </tr>
            <tr v-if="!dados.movimentos.length"><td colspan="5" class="vazio">Nenhum movimento ainda.</td></tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <Modal v-if="modal" :titulo="form.tipo === 'entrada' ? 'Registrar entrada' : 'Registrar saída'"
           :sub="form.tipo === 'entrada' ? 'ensilagem ou compra de volumoso' : 'consumo do cocho'" @fechar="modal = false">
      <div class="mform">
        <div class="field"><label>Quantidade (toneladas) *</label>
          <input class="input tnum" type="number" v-model="form.quantidade_t" placeholder="ex: 100" />
          <span class="hint">Quanto entrou/saiu, em toneladas de volumoso.</span>
        </div>
        <div class="field"><label>Descrição</label>
          <input class="input" v-model="form.descricao" :placeholder="form.tipo === 'entrada' ? 'ex: Ensilagem milho' : 'ex: Consumo cocho'" />
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
.selc { width: auto; min-width: 240px; appearance: auto; }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 520px; border-collapse: collapse; table-layout: fixed; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.mform { display: flex; flex-direction: column; gap: 14px; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
.mform .hint { font-size: 12px; color: var(--muted); }
</style>
