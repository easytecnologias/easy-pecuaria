<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ArrowDownCircle, ArrowUpCircle, AlertTriangle, CalendarClock, Plus, Pencil, Trash2, Check } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getContas, criarConta, editarConta, baixarConta, excluirConta,
  TIPOS_CONTA, TIPOS_DOCUMENTO,
  type Fazenda, type ResumoContas, type Conta,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const dados = ref<ResumoContas | null>(null);
const erro = ref("");

const fTipo = ref("");
const fSituacao = ref("abertas");

const hoje = new Date().toISOString().slice(0, 10);
const fmtData = (d: string | null) => (d ? d.split("-").reverse().join("/") : "—");
const brl = (v: number) => `R$ ${v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const rotDoc = (d: string) => TIPOS_DOCUMENTO.find((x) => x.valor === d)?.rotulo ?? d;

const lista = computed(() => {
  let l = dados.value?.contas ?? [];
  if (fTipo.value) l = l.filter((c) => c.tipo === fTipo.value);
  if (fSituacao.value === "abertas") l = l.filter((c) => c.status === "aberto");
  else if (fSituacao.value === "vencidas") l = l.filter((c) => c.situacao === "vencida");
  else if (fSituacao.value === "vencendo") l = l.filter((c) => c.situacao === "vence_em_breve");
  else if (fSituacao.value === "baixadas") l = l.filter((c) => c.status === "baixado");
  return l;
});

function rotSituacao(c: Conta) {
  if (c.status === "baixado") return c.tipo === "pagar" ? "Paga" : "Recebida";
  if (c.situacao === "vencida") return `Venceu há ${-c.dias} d`;
  if (c.situacao === "vence_em_breve") return c.dias === 0 ? "Vence hoje" : `Vence em ${c.dias} d`;
  return `Em ${c.dias} d`;
}
function classeSituacao(c: Conta) {
  if (c.status === "baixado") return "OK";
  if (c.situacao === "vencida") return "ALERTA";
  if (c.situacao === "vence_em_breve") return "REVISAR";
  return "OK";
}

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try { dados.value = await getContas(fazendaId.value); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  if (fazendas.value[0]) { fazendaId.value = fazendas.value[0].id; await carregar(); }
}
watch(fazendaId, (_v, old) => { if (old) carregar(); });
onMounted(init);

// --- nova conta / edicao ---
const modal = ref(false);
const editando = ref<Conta | null>(null);
const vazio = {
  tipo: "pagar", descricao: "", categoria: "", contraparte: "",
  documento: "duplicata", numero_documento: "", valor: "",
  emissao: "", vencimento: "", observacao: "",
};
const form = ref({ ...vazio });
const erroModal = ref("");
const salvando = ref(false);

function abrirNova(tipo = "pagar") {
  editando.value = null;
  form.value = { ...vazio, tipo, vencimento: hoje };
  erroModal.value = ""; modal.value = true;
}
function abrirEdicao(c: Conta) {
  editando.value = c;
  form.value = {
    tipo: c.tipo, descricao: c.descricao, categoria: c.categoria,
    contraparte: c.contraparte ?? "", documento: c.documento,
    numero_documento: c.numero_documento ?? "", valor: c.valor.toString(),
    emissao: c.emissao ?? "", vencimento: c.vencimento, observacao: c.observacao ?? "",
  };
  erroModal.value = ""; modal.value = true;
}

async function salvar() {
  if (!form.value.descricao.trim()) { erroModal.value = "Descreva a conta."; return; }
  if (!form.value.categoria.trim()) { erroModal.value = "Informe a categoria."; return; }
  if (!Number(form.value.valor)) { erroModal.value = "Informe o valor."; return; }
  if (!form.value.vencimento) { erroModal.value = "Informe o vencimento."; return; }
  salvando.value = true; erroModal.value = "";
  const body: any = {
    tipo: form.value.tipo, descricao: form.value.descricao.trim(),
    categoria: form.value.categoria.trim(), contraparte: form.value.contraparte || null,
    documento: form.value.documento, numero_documento: form.value.numero_documento || null,
    valor: Number(form.value.valor), emissao: form.value.emissao || null,
    vencimento: form.value.vencimento, observacao: form.value.observacao || null,
  };
  try {
    if (editando.value) await editarConta(editando.value.id, body);
    else await criarConta(fazendaId.value, body);
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}

// --- baixa ---
const modalBaixa = ref(false);
const alvo = ref<Conta | null>(null);
const baixaData = ref(hoje);
const baixaValor = ref("");
function abrirBaixa(c: Conta) {
  alvo.value = c; baixaData.value = hoje; baixaValor.value = c.valor.toString();
  modalBaixa.value = true;
}
async function confirmarBaixa() {
  if (!alvo.value) return;
  try {
    await baixarConta(alvo.value.id, { data_baixa: baixaData.value, valor_pago: Number(baixaValor.value) });
    modalBaixa.value = false; await carregar();
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function remover(c: Conta) {
  if (!confirm(`Excluir "${c.descricao}"?`)) return;
  try { await excluirConta(c.id); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell title="Contas" sub="A pagar, a receber e vencimentos" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Financeiro</div>
      <h1>Contas a pagar e a receber</h1>
      <p>Lance a duplicata, o boleto ou a nota com o <b>vencimento</b>. A tela avisa o que está vencendo e, quando você dá baixa, o valor entra automaticamente no caixa do Financeiro.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="A pagar" :value="brl(dados.total_a_pagar)" sub="em aberto"
               :icon="ArrowUpCircle" tone="danger" />
      <KpiCard label="A receber" :value="brl(dados.total_a_receber)" sub="em aberto"
               :icon="ArrowDownCircle" tone="primary" />
      <KpiCard label="Saldo previsto" :value="brl(dados.saldo_previsto)" sub="receber − pagar"
               emoji="⚖️" :tone="dados.saldo_previsto >= 0 ? 'blue' : 'danger'" />
      <KpiCard label="Vencidas" :value="dados.vencidas" :sub="brl(dados.valor_vencido)"
               :icon="AlertTriangle" :tone="dados.vencidas > 0 ? 'danger' : 'primary'" />
    </div>

    <!-- audio 9: "quando as duplicatas e os boletos estiverem vencendo" -->
    <div v-if="dados && (dados.vencidas > 0 || dados.vencendo > 0)" class="aviso">
      <CalendarClock :size="18" />
      <div class="aviso__txt">
        <b>{{ dados.vencidas + dados.vencendo }}</b>
        {{ dados.vencidas + dados.vencendo === 1 ? "conta precisa" : "contas precisam" }}
        de atenção — {{ dados.vencidas }} vencida(s) e {{ dados.vencendo }} vencendo em até {{ dados.janela_aviso_dias }} dias.
        <div class="lista-aviso">
          <span v-for="(a, i) in dados.avisos.slice(0, 4)" :key="i" class="chip">{{ a }}</span>
          <span v-if="dados.avisos.length > 4" class="muted">+{{ dados.avisos.length - 4 }}</span>
        </div>
      </div>
      <button class="btn btn--secondary btnp" @click="fSituacao = 'vencidas'">Ver vencidas</button>
    </div>

    <Panel title="Contas" sub="filtre por tipo ou situação" v-if="dados">
      <template #actions>
        <button class="btn btn--secondary" style="height:34px" @click="abrirNova('receber')">
          <Plus :size="15" /> A receber
        </button>
        <button class="btn btn--primary" style="height:34px" @click="abrirNova('pagar')">
          <Plus :size="15" /> A pagar
        </button>
      </template>

      <div class="filtros">
        <select class="input selc" v-model="fSituacao">
          <option value="abertas">Em aberto</option>
          <option value="vencidas">Vencidas</option>
          <option value="vencendo">Vencendo</option>
          <option value="baixadas">Baixadas</option>
          <option value="">Todas</option>
        </select>
        <select class="input selc" v-model="fTipo">
          <option value="">Pagar e receber</option>
          <option v-for="t in TIPOS_CONTA" :key="t.valor" :value="t.valor">{{ t.rotulo }}</option>
        </select>
      </div>

      <div class="tbl-wrap">
        <table class="tbl">
          <thead>
            <tr><th>Conta</th><th>Documento</th><th>Contraparte</th><th class="num">Valor</th>
                <th>Vencimento</th><th>Situação</th><th class="num">Ações</th></tr>
          </thead>
          <tbody>
            <tr v-for="c in lista" :key="c.id" :class="{ venc: c.situacao === 'vencida' && c.status === 'aberto' }">
              <td>
                <span class="seta" :class="c.tipo">{{ c.tipo === "pagar" ? "↑" : "↓" }}</span>
                <b>{{ c.descricao }}</b>
                <div class="muted sub">{{ c.categoria }}</div>
              </td>
              <td class="muted">
                {{ rotDoc(c.documento) }}
                <div v-if="c.numero_documento" class="muted sub">nº {{ c.numero_documento }}</div>
              </td>
              <td class="muted">{{ c.contraparte ?? "—" }}</td>
              <td class="num tnum"><b>{{ brl(c.valor) }}</b></td>
              <td class="tnum">{{ fmtData(c.vencimento) }}</td>
              <td>
                <span class="badge" :class="classeSituacao(c)"><span class="dot" />{{ rotSituacao(c) }}</span>
                <div v-if="c.data_baixa" class="muted sub">em {{ fmtData(c.data_baixa) }}</div>
              </td>
              <td class="num acoes">
                <button v-if="c.status === 'aberto'" class="btn btn--primary btnp" @click="abrirBaixa(c)">
                  <Check :size="13" /> Baixar
                </button>
                <button v-if="c.status === 'aberto'" class="iconbtn" @click="abrirEdicao(c)"><Pencil :size="14" /></button>
                <button class="iconbtn danger" @click="remover(c)"><Trash2 :size="14" /></button>
              </td>
            </tr>
            <tr v-if="!lista.length"><td colspan="7" class="vazio">Nenhuma conta com esse filtro.</td></tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <Modal v-if="modal" :titulo="editando ? 'Editar conta' : (form.tipo === 'pagar' ? 'Nova conta a pagar' : 'Nova conta a receber')"
           sub="documento, valor e vencimento" @fechar="modal = false">
      <div class="mform">
        <div class="dupla">
          <div class="field"><label>Tipo *</label>
            <select class="input" v-model="form.tipo">
              <option v-for="t in TIPOS_CONTA" :key="t.valor" :value="t.valor">{{ t.rotulo }}</option>
            </select>
          </div>
          <div class="field"><label>Categoria *</label>
            <input class="input" v-model="form.categoria" placeholder="ex: Ração, Venda de boi" />
          </div>
        </div>
        <div class="field"><label>Descrição *</label>
          <input class="input" v-model="form.descricao" placeholder="ex: Duplicata ração setembro" />
        </div>
        <div class="field"><label>Fornecedor / Cliente</label>
          <input class="input" v-model="form.contraparte" placeholder="quem recebe ou quem paga" />
        </div>

        <div class="secao">Documento</div>
        <div class="dupla">
          <div class="field"><label>Tipo de documento</label>
            <select class="input" v-model="form.documento">
              <option v-for="d in TIPOS_DOCUMENTO" :key="d.valor" :value="d.valor">{{ d.rotulo }}</option>
            </select>
          </div>
          <div class="field"><label>Número</label>
            <input class="input" v-model="form.numero_documento" placeholder="opcional" />
          </div>
        </div>

        <div class="secao">Valores e prazo</div>
        <div class="tripla">
          <div class="field"><label>Valor (R$) *</label>
            <input class="input tnum" type="number" step="0.01" v-model="form.valor" placeholder="1500,00" />
          </div>
          <div class="field"><label>Emissão</label>
            <input class="input" type="date" v-model="form.emissao" />
          </div>
          <div class="field"><label>Vencimento *</label>
            <input class="input" type="date" v-model="form.vencimento" />
          </div>
        </div>
        <div class="field"><label>Observação</label>
          <input class="input" v-model="form.observacao" placeholder="opcional" />
        </div>
        <p v-if="erroModal" class="error">{{ erroModal }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modal = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvando" @click="salvar">Salvar</button>
      </template>
    </Modal>

    <Modal v-if="modalBaixa" :titulo="alvo?.tipo === 'pagar' ? 'Dar baixa (pagamento)' : 'Dar baixa (recebimento)'"
           :sub="alvo?.descricao" @fechar="modalBaixa = false">
      <div class="mform">
        <div class="dupla">
          <div class="field"><label>Data</label>
            <input class="input" type="date" v-model="baixaData" />
          </div>
          <div class="field"><label>Valor (R$)</label>
            <input class="input tnum" type="number" step="0.01" v-model="baixaValor" />
            <span class="hint">Pode ajustar se houve juros ou desconto.</span>
          </div>
        </div>
        <p class="muted dica">O valor entra no caixa do Financeiro como
          {{ alvo?.tipo === "pagar" ? "despesa" : "receita" }}.</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modalBaixa = false">Cancelar</button>
        <button class="btn btn--primary" @click="confirmarBaixa">Confirmar baixa</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.selc { width: auto; min-width: 180px; appearance: auto; }
.filtros { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.aviso { display: flex; align-items: flex-start; gap: 10px; background: #fff8ef; border: 1px solid #f0dcc0;
  color: #8a5a12; border-radius: 8px; padding: 12px 14px; margin-bottom: 16px; font-size: 14px; flex-wrap: wrap; }
.aviso__txt { flex: 1; min-width: 220px; }
.lista-aviso { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.chip { background: #fff; border: 1px solid #f0dcc0; border-radius: 999px; padding: 2px 10px; font-size: 12px; }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 900px; border-collapse: collapse; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.tbl tr.venc td { background: #fffaf5; }
.seta { font-weight: 700; margin-right: 6px; }
.seta.pagar { color: var(--danger); }
.seta.receber { color: var(--primary); }
.sub { font-size: 12px; margin-top: 2px; }
.acoes { white-space: nowrap; display: flex; gap: 6px; justify-content: flex-end; align-items: center; }
.btnp { height: 30px; padding: 0 12px; font-size: 13px; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn:hover { color: var(--primary); border-color: var(--primary); }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.mform { display: flex; flex-direction: column; gap: 14px; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
.mform .hint { font-size: 12px; color: var(--muted); }
.dica { font-size: 13px; }
.dupla { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.tripla { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.secao { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted);
  font-weight: 700; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
@media (max-width: 700px) { .dupla, .tripla { grid-template-columns: 1fr; } }
</style>
