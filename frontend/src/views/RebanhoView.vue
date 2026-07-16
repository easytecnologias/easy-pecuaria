<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ChevronRight, Pencil, Trash2, Plus } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getLotes, getAnimais, criarLote, atualizarLote, excluirLote,
  type Fazenda, type Lote, type Animal,
} from "../api";

const router = useRouter();
const SEM_LOTE = "__sem_lote__";
const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref<string>("");
const lotes = ref<Lote[]>([]);
const todos = ref<Animal[]>([]);
const loteSel = ref<Lote | null>(null);
const animais = ref<Animal[]>([]);
const erro = ref("");
const carregando = ref(false);

const CONF = ["Engorda", "Confinamento"];
// total e categorias saem dos animais (inclui os sem lote); confinamento vem dos lotes
const totalAnimais = computed(() => todos.value.length);
const matrizes = computed(() => todos.value.filter((a) => a.categoria === "Matriz").length);
const bezerros = computed(() =>
  todos.value.filter((a) => (a.categoria ?? "").startsWith("Bezerr")).length
);
const emConfinamento = computed(() =>
  lotes.value.filter((l) => CONF.includes(l.categoria ?? "")).reduce((s, l) => s + l.n_animais, 0)
);

const semLoteCount = computed(() => todos.value.filter((a) => !a.lote_id).length);
// lista de lotes exibida: os reais + um grupo virtual "Sem lote" quando houver animais soltos
const lotesView = computed<Lote[]>(() => {
  const base = [...lotes.value];
  if (semLoteCount.value > 0) {
    base.push({ id: SEM_LOTE, nome: "Sem lote", categoria: null, local: null,
      ativo: true, n_animais: semLoteCount.value });
  }
  return base;
});

function selecionarLote(l: Lote) {
  loteSel.value = l;
  animais.value = l.id === SEM_LOTE
    ? todos.value.filter((a) => !a.lote_id)
    : todos.value.filter((a) => a.lote_id === l.id);
}

async function carregarDados() {
  if (!fazendaId.value) return;
  erro.value = "";
  carregando.value = true;
  try {
    [lotes.value, todos.value] = await Promise.all([
      getLotes(fazendaId.value), getAnimais(fazendaId.value),
    ]);
    const view = lotesView.value;
    if (view.length) selecionarLote(view[0]);
    else { loteSel.value = null; animais.value = []; }
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
  finally { carregando.value = false; }
}

async function init() {
  fazendas.value = await getFazendas();
  if (!fazendas.value.length) return;
  fazendaId.value = fazendas.value[0].id;
  await carregarDados();
}

watch(fazendaId, (_v, old) => { if (old) carregarDados(); });
onMounted(init);

// ---- CRUD de lote (modal) ----
const CATS_LOTE = ["Matrizes", "Engorda", "Bezerros", "Novilhas", "Recria"];
const modalAberto = ref(false);
const editando = ref<Lote | null>(null);      // null = criando
const form = ref({ nome: "", categoria: "Engorda", local: "" });
const erroModal = ref("");
const salvandoModal = ref(false);

function abrirNovo() {
  editando.value = null;
  form.value = { nome: "", categoria: "Engorda", local: "" };
  erroModal.value = "";
  modalAberto.value = true;
}
function abrirEdicao(l: Lote, ev: Event) {
  ev.stopPropagation();
  editando.value = l;
  form.value = { nome: l.nome, categoria: l.categoria ?? "Engorda", local: l.local ?? "" };
  erroModal.value = "";
  modalAberto.value = true;
}
async function salvarLote() {
  if (!form.value.nome.trim()) { erroModal.value = "Dê um nome ao lote."; return; }
  salvandoModal.value = true; erroModal.value = "";
  try {
    if (editando.value) await atualizarLote(fazendaId.value, editando.value.id, { ...form.value });
    else await criarLote(fazendaId.value, { ...form.value });
    modalAberto.value = false;
    await carregarDados();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvandoModal.value = false; }
}
async function removerLote(l: Lote, ev: Event) {
  ev.stopPropagation();
  if (!confirm(`Excluir o lote "${l.nome}"? Esta ação não pode ser desfeita.`)) return;
  erro.value = "";
  try { await excluirLote(fazendaId.value, l.id); await carregarDados(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell title="Rebanho" sub="Lotes e animais" @refresh="carregarDados">
    <div class="head">
      <div class="eyebrow">Cadastro base</div>
      <h1>Rebanho por lote</h1>
      <p>Os animais vivem em lotes (grupos de manejo). Clique num animal para ver a ficha e registrar pesagens — é onde o dado vira indicador.</p>
    </div>

    <div class="row" style="margin-bottom:18px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input sel" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <div class="metrics">
      <KpiCard label="Total de animais" :value="totalAnimais" sub="na fazenda" emoji="🐂" tone="blue" />
      <KpiCard label="Matrizes" :value="matrizes" sub="em reprodução" emoji="🐄" tone="primary" />
      <KpiCard label="Em confinamento" :value="emConfinamento" sub="engorda" emoji="🌾" tone="amber" />
      <KpiCard label="Bezerros(as)" :value="bezerros" sub="cria" emoji="🍼" tone="purple" />
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="painel-grid">
      <Panel title="Lotes" sub="Clique para ver os animais">
        <template #actions>
          <button class="btn btn--secondary" style="height:34px" @click="abrirNovo"><Plus :size="15" /> Novo lote</button>
        </template>
        <div class="tbl-wrap">
        <table class="tbl">
          <colgroup><col style="width:34%" /><col style="width:20%" /><col style="width:15%" /><col style="width:11%" /><col style="width:20%" /></colgroup>
          <thead><tr><th>Lote</th><th>Categoria</th><th>Local</th><th class="num">Animais</th><th class="num">Ações</th></tr></thead>
          <tbody>
            <tr v-for="l in lotesView" :key="l.id" @click="selecionarLote(l)"
                :class="{ selrow: loteSel?.id === l.id, virtual: l.id === SEM_LOTE }">
              <td><strong>{{ l.nome }}</strong></td>
              <td><span v-if="l.id !== SEM_LOTE" class="tag">{{ l.categoria ?? "—" }}</span><span v-else class="muted">—</span></td>
              <td class="muted">{{ l.local ?? "—" }}</td>
              <td class="num tnum"><span class="count">{{ l.n_animais }}</span></td>
              <td class="num acoes">
                <template v-if="l.id !== SEM_LOTE">
                  <button class="iconbtn" title="Editar" @click="abrirEdicao(l, $event)"><Pencil :size="15" /></button>
                  <button class="iconbtn danger" title="Excluir" @click="removerLote(l, $event)"><Trash2 :size="15" /></button>
                </template>
              </td>
            </tr>
            <tr v-if="!lotesView.length && !carregando"><td colspan="5" class="vazio">Nenhum animal nesta fazenda ainda.</td></tr>
          </tbody>
        </table>
        </div>
      </Panel>

      <Panel :title="loteSel?.nome ?? 'Animais'" sub="animais do lote">
        <div class="tbl-wrap">
        <table class="tbl">
          <colgroup><col style="width:44%" /><col style="width:30%" /><col style="width:14%" /><col style="width:12%" /></colgroup>
          <thead><tr><th>Brinco</th><th>Raça</th><th>Sexo</th><th></th></tr></thead>
          <tbody>
            <tr v-for="a in animais" :key="a.id" @click="router.push(`/animais/${a.id}`)">
              <td><strong>{{ a.brinco }}</strong><div class="muted sub">{{ a.categoria }}</div></td>
              <td class="muted">{{ a.raca ?? "—" }}</td>
              <td>{{ a.sexo ?? "—" }}</td>
              <td class="num"><ChevronRight :size="16" class="muted" /></td>
            </tr>
            <tr v-if="!animais.length"><td colspan="4" class="vazio">Selecione um lote.</td></tr>
          </tbody>
        </table>
        </div>
      </Panel>
    </div>

    <Modal
      v-if="modalAberto"
      :titulo="editando ? 'Editar lote' : 'Novo lote'"
      sub="uma turma de animais manejada junta"
      @fechar="modalAberto = false"
    >
      <div class="mform">
        <div class="field"><label>Nome do lote *</label>
          <input class="input" v-model="form.nome" placeholder="ex: Garrotes Confinamento A" @keyup.enter="salvarLote" />
        </div>
        <div class="field"><label>Categoria</label>
          <select class="input selc" v-model="form.categoria">
            <option v-for="c in CATS_LOTE" :key="c">{{ c }}</option>
          </select>
        </div>
        <div class="field"><label>Local</label>
          <input class="input" v-model="form.local" placeholder="ex: Pasto 3, Curral 1" />
        </div>
        <p v-if="erroModal" class="error">{{ erroModal }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modalAberto = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvandoModal" @click="salvarLote">
          {{ editando ? "Salvar" : "Criar lote" }}
        </button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.sel { width: auto; min-width: 240px; appearance: auto; }

.painel-grid { display: grid; grid-template-columns: 1.25fr 1fr; gap: 24px; align-items: stretch; }
@media (max-width: 900px) { .painel-grid { grid-template-columns: 1fr; } }

/* tabelas com colunas espaçadas e números alinhados à direita */
.tbl { width: 100%; min-width: 380px; border-collapse: collapse; table-layout: fixed; }
.tbl th, .tbl td { padding: 12px 14px; text-align: left; vertical-align: middle; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted);
  font-weight: 600; border-bottom: 1px solid var(--border); }
.tbl td { border-bottom: 1px solid var(--border); font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl tbody tr { cursor: pointer; }
.tbl tbody tr:hover td { background: #fafbfc; }
.tbl tr.selrow td { background: #eef7f2; }
.tbl tr.virtual td:first-child strong { color: var(--muted); font-style: italic; }
.tbl-wrap { overflow-x: auto; }
.tbl .num { text-align: right; }
.tbl .sub { font-size: 12px; }
.count { display: inline-block; min-width: 30px; padding: 2px 9px; border-radius: 999px;
  background: #eef2f4; color: var(--text); font-weight: 700; font-size: 13px; }
.vazio { text-align: center; padding: 22px; color: var(--muted); }

.acoes { white-space: nowrap; overflow: visible; text-overflow: clip; }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 30px; height: 30px; border-radius: 7px; cursor: pointer; display: inline-grid; place-items: center;
  margin-left: 6px; vertical-align: middle; }
.iconbtn:hover { background: #f2f8f5; color: var(--primary); border-color: #bfe0d0; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }

.mform { display: flex; flex-direction: column; gap: 14px; }
.mform .field label { font-size: 13px; font-weight: 600; color: var(--text); }
.selc { appearance: auto; }
</style>
