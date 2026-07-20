<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ClipboardList, AlertTriangle, CalendarDays, CheckCircle2, Plus, Trash2, UserCheck } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getPlanejamento, criarAtividade, concluirAtividade, excluirAtividade,
  getUsuarios, getMeCached,
  PERIODOS, TIPOS_ATIVIDADE,
  type Fazenda, type ResumoPlanejamento, type Atividade, type UsuarioAdmin,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const dados = ref<ResumoPlanejamento | null>(null);
const usuarios = ref<UsuarioAdmin[]>([]);
const meuId = ref("");
const erro = ref("");

const fPeriodo = ref("");
const fStatus = ref("abertas");

const hoje = new Date().toISOString().slice(0, 10);
const fmtData = (d: string | null) => (d ? d.split("-").reverse().join("/") : "—");
const rotTipo = (t: string) => TIPOS_ATIVIDADE.find((x) => x.valor === t)?.rotulo ?? t;
const rotPeriodo = (p: string) => PERIODOS.find((x) => x.valor === p)?.rotulo ?? p;
const pct = (v: number | null) => (v === null ? "—" : `${(v * 100).toFixed(0)}%`);

const atrasada = (a: Atividade) => a.status !== "concluida" && a.data_prevista < hoje;

const lista = computed(() => {
  let l = dados.value?.atividades ?? [];
  if (fPeriodo.value) l = l.filter((a) => a.periodo === fPeriodo.value);
  if (fStatus.value === "abertas") l = l.filter((a) => a.status !== "concluida" && a.status !== "cancelada");
  else if (fStatus.value === "concluidas") l = l.filter((a) => a.status === "concluida");
  else if (fStatus.value === "minhas") l = l.filter((a) => a.responsavel_id === meuId.value && a.status !== "concluida");
  return l;
});

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try { dados.value = await getPlanejamento(fazendaId.value); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  try { meuId.value = (await getMeCached()).id; } catch { /* ok */ }
  try { usuarios.value = await getUsuarios(); } catch { usuarios.value = []; }  // só admin enxerga
  if (fazendas.value[0]) { fazendaId.value = fazendas.value[0].id; await carregar(); }
}
watch(fazendaId, (_v, old) => { if (old) carregar(); });
onMounted(init);

// --- nova atividade ---
const modal = ref(false);
const form = ref({ titulo: "", descricao: "", tipo: "manejo_rebanho", periodo: "semanal", data_prevista: "", responsavel_id: "" });
const erroModal = ref("");
const salvando = ref(false);

function abrir() {
  form.value = { titulo: "", descricao: "", tipo: "manejo_rebanho", periodo: "semanal", data_prevista: hoje, responsavel_id: "" };
  erroModal.value = ""; modal.value = true;
}
async function salvar() {
  if (!form.value.titulo.trim()) { erroModal.value = "Descreva a atividade."; return; }
  if (!form.value.data_prevista) { erroModal.value = "Informe a data prevista."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    await criarAtividade(fazendaId.value, {
      titulo: form.value.titulo.trim(),
      descricao: form.value.descricao || null,
      tipo: form.value.tipo, periodo: form.value.periodo,
      data_prevista: form.value.data_prevista,
      responsavel_id: form.value.responsavel_id || null,
    });
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}

// --- concluir ---
const modalOk = ref(false);
const alvo = ref<Atividade | null>(null);
const obsConclusao = ref("");
function abrirConcluir(a: Atividade) { alvo.value = a; obsConclusao.value = ""; modalOk.value = true; }
async function confirmarConclusao() {
  if (!alvo.value) return;
  try { await concluirAtividade(alvo.value.id, obsConclusao.value || undefined); modalOk.value = false; await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function remover(a: Atividade) {
  if (!confirm(`Excluir a atividade "${a.titulo}"?`)) return;
  try { await excluirAtividade(a.id); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell title="Planejamento" sub="Atividades com responsável e acompanhamento" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Gestão</div>
      <h1>Planejamento de atividades</h1>
      <p>Lance a atividade (manejo, sanitário, pesagem...), defina <b>quem executa</b> e o <b>prazo</b>. A pessoa vê o que tem pra fazer em <b>"Minhas"</b> e marca como concluída — e você acompanha os números.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="Em aberto" :value="dados.abertas" sub="a executar" :icon="ClipboardList" tone="primary" />
      <KpiCard label="Atrasadas" :value="dados.atrasadas" sub="passaram do prazo" :icon="AlertTriangle"
               :tone="dados.atrasadas > 0 ? 'danger' : 'primary'" />
      <KpiCard label="Desta semana" :value="dados.da_semana" sub="próximos 7 dias" :icon="CalendarDays" tone="blue" />
      <KpiCard label="Taxa de conclusão" :value="pct(dados.taxa_conclusao)"
               :sub="`${dados.concluidas} concluídas`" :icon="CheckCircle2" tone="amber" />
    </div>

    <div v-if="dados && dados.minhas_pendentes > 0" class="aviso">
      <UserCheck :size="18" />
      <span>Você tem <b>{{ dados.minhas_pendentes }}</b> {{ dados.minhas_pendentes === 1 ? 'atividade' : 'atividades' }} para executar.</span>
      <button class="btn btn--secondary btnp" @click="fStatus = 'minhas'">Ver minhas</button>
    </div>

    <Panel title="Atividades" sub="filtre por período ou situação" v-if="dados">
      <template #actions>
        <button class="btn btn--primary" style="height:34px" @click="abrir"><Plus :size="15" /> Nova atividade</button>
      </template>

      <div class="filtros">
        <select class="input selc" v-model="fStatus">
          <option value="abertas">Em aberto</option>
          <option value="minhas">Minhas pendentes</option>
          <option value="concluidas">Concluídas</option>
          <option value="">Todas</option>
        </select>
        <select class="input selc" v-model="fPeriodo">
          <option value="">Todos os períodos</option>
          <option v-for="p in PERIODOS" :key="p.valor" :value="p.valor">{{ p.rotulo }}</option>
        </select>
      </div>

      <div class="tbl-wrap">
        <table class="tbl">
          <thead>
            <tr><th>Atividade</th><th>Tipo</th><th>Período</th><th>Prazo</th><th>Responsável</th><th>Situação</th><th class="num">Ações</th></tr>
          </thead>
          <tbody>
            <tr v-for="a in lista" :key="a.id" :class="{ atr: atrasada(a) }">
              <td>
                <b>{{ a.titulo }}</b>
                <div v-if="a.descricao" class="muted sub">{{ a.descricao }}</div>
              </td>
              <td class="muted">{{ rotTipo(a.tipo) }}</td>
              <td class="muted">{{ rotPeriodo(a.periodo) }}</td>
              <td :class="atrasada(a) ? 'atraso' : ''">{{ fmtData(a.data_prevista) }}</td>
              <td class="muted">{{ a.responsavel_nome ?? "—" }}</td>
              <td>
                <span v-if="a.status === 'concluida'" class="badge OK"><span class="dot" />Concluída</span>
                <span v-else-if="atrasada(a)" class="badge ALERTA"><span class="dot" />Atrasada</span>
                <span v-else class="badge REVISAR"><span class="dot" />Pendente</span>
                <div v-if="a.status === 'concluida'" class="muted sub">por {{ a.concluida_por_nome ?? "—" }}</div>
              </td>
              <td class="num acoes">
                <button v-if="a.status !== 'concluida'" class="btn btn--primary btnp" @click="abrirConcluir(a)">Concluir</button>
                <button class="iconbtn danger" @click="remover(a)"><Trash2 :size="14" /></button>
              </td>
            </tr>
            <tr v-if="!lista.length"><td colspan="7" class="vazio">Nenhuma atividade com esse filtro.</td></tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <Modal v-if="modal" titulo="Nova atividade" sub="o que precisa ser feito e por quem" @fechar="modal = false">
      <div class="mform">
        <div class="field"><label>Atividade *</label>
          <input class="input" v-model="form.titulo" placeholder="ex: Vacinar lote da Perucaba" />
        </div>
        <div class="field"><label>Detalhes</label>
          <input class="input" v-model="form.descricao" placeholder="opcional" />
        </div>
        <div class="dupla">
          <div class="field"><label>Tipo</label>
            <select class="input" v-model="form.tipo">
              <option v-for="t in TIPOS_ATIVIDADE" :key="t.valor" :value="t.valor">{{ t.rotulo }}</option>
            </select>
          </div>
          <div class="field"><label>Período</label>
            <select class="input" v-model="form.periodo">
              <option v-for="p in PERIODOS" :key="p.valor" :value="p.valor">{{ p.rotulo }}</option>
            </select>
          </div>
        </div>
        <div class="dupla">
          <div class="field"><label>Prazo *</label>
            <input class="input" type="date" v-model="form.data_prevista" />
          </div>
          <div class="field"><label>Responsável</label>
            <select class="input" v-model="form.responsavel_id">
              <option value="">— sem responsável —</option>
              <option v-for="u in usuarios" :key="u.id" :value="u.id">{{ u.nome }}</option>
            </select>
            <span class="hint">Ela verá em "Minhas pendentes".</span>
          </div>
        </div>
        <p v-if="erroModal" class="error">{{ erroModal }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modal = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvando" @click="salvar">Lançar</button>
      </template>
    </Modal>

    <Modal v-if="modalOk" titulo="Concluir atividade" :sub="alvo?.titulo" @fechar="modalOk = false">
      <div class="mform">
        <div class="field"><label>Como foi? (opcional)</label>
          <input class="input" v-model="obsConclusao" placeholder="ex: feito, 3 animais ficaram para amanhã" />
        </div>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modalOk = false">Cancelar</button>
        <button class="btn btn--primary" @click="confirmarConclusao">Marcar como concluída</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.selc { width: auto; min-width: 180px; appearance: auto; }
.filtros { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.aviso { display: flex; align-items: center; gap: 10px; background: #eef7f3; border: 1px solid #cce5da;
  color: #14543f; border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; font-size: 14px; flex-wrap: wrap; }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 820px; border-collapse: collapse; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.tbl tr.atr td { background: #fffaf5; }
.atraso { color: var(--danger); font-weight: 600; }
.sub { font-size: 12px; margin-top: 2px; }
.acoes { white-space: nowrap; display: flex; gap: 6px; justify-content: flex-end; align-items: center; }
.btnp { height: 30px; padding: 0 12px; font-size: 13px; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.mform { display: flex; flex-direction: column; gap: 14px; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
.mform .hint { font-size: 12px; color: var(--muted); }
.dupla { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 700px) { .dupla { grid-template-columns: 1fr; } }
</style>
