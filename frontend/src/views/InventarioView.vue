<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Boxes, Tractor, MapPin, Wallet, Plus, Pencil, Trash2, ArrowLeftRight, History } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getInventario, criarItemInventario, editarItemInventario,
  excluirItemInventario, movimentarItem, getMovimentosItem,
  CATEGORIAS_ITEM,
  type Fazenda, type ResumoInventario, type ItemInventario, type MovimentoInventario,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const dados = ref<ResumoInventario | null>(null);
const erro = ref("");

const busca = ref("");
const fCategoria = ref("");

const fmtData = (d: string | null) => (d ? d.split("-").reverse().join("/") : "—");
const rotuloCat = (c: string) => CATEGORIAS_ITEM.find((x) => x.valor === c)?.rotulo ?? c;
const brl = (v: number | null) =>
  v === null || v === undefined ? "—" : v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const itensMostrados = computed(() => {
  let lista = dados.value?.itens ?? [];
  if (fCategoria.value) lista = lista.filter((i) => i.categoria === fCategoria.value);
  const q = busca.value.trim().toLowerCase();
  if (q) {
    lista = lista.filter((i) =>
      [i.nome, i.identificacao, i.localizacao].some((c) => (c ?? "").toLowerCase().includes(q))
    );
  }
  return lista;
});
const nMaquinas = computed(() => dados.value?.por_categoria["maquina"] ?? 0);

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try { dados.value = await getInventario(fazendaId.value); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  if (fazendas.value[0]) { fazendaId.value = fazendas.value[0].id; await carregar(); }
}
watch(fazendaId, (_v, old) => { if (old) carregar(); });
onMounted(init);

// --- item (novo/editar) ---
const modal = ref(false);
const editando = ref<ItemInventario | null>(null);
const form = ref({
  categoria: "equipamento", nome: "", identificacao: "", localizacao: "",
  quantidade: "", unidade: "", valor: "", situacao: "ativo", data_aquisicao: "", observacao: "",
});
const erroModal = ref("");
const salvando = ref(false);

function abrirNovo() {
  editando.value = null;
  form.value = { categoria: "equipamento", nome: "", identificacao: "", localizacao: "",
    quantidade: "", unidade: "", valor: "", situacao: "ativo", data_aquisicao: "", observacao: "" };
  erroModal.value = ""; modal.value = true;
}
function abrirEdicao(i: ItemInventario) {
  editando.value = i;
  form.value = {
    categoria: i.categoria, nome: i.nome, identificacao: i.identificacao ?? "",
    localizacao: i.localizacao ?? "", quantidade: i.quantidade?.toString() ?? "",
    unidade: i.unidade ?? "", valor: i.valor?.toString() ?? "", situacao: i.situacao,
    data_aquisicao: i.data_aquisicao ?? "", observacao: i.observacao ?? "",
  };
  erroModal.value = ""; modal.value = true;
}
async function salvar() {
  if (!form.value.nome.trim()) { erroModal.value = "Informe o nome do item."; return; }
  salvando.value = true; erroModal.value = "";
  const body: any = {
    categoria: form.value.categoria, nome: form.value.nome.trim(),
    identificacao: form.value.identificacao || null, localizacao: form.value.localizacao || null,
    quantidade: form.value.quantidade ? parseFloat(form.value.quantidade) : null,
    unidade: form.value.unidade || null,
    valor: form.value.valor ? parseFloat(form.value.valor) : null,
    situacao: form.value.situacao, data_aquisicao: form.value.data_aquisicao || null,
    observacao: form.value.observacao || null,
  };
  try {
    if (editando.value) await editarItemInventario(editando.value.id, body);
    else await criarItemInventario(fazendaId.value, body);
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
async function remover(i: ItemInventario) {
  if (!confirm(`Excluir "${i.nome}" do inventário?`)) return;
  try { await excluirItemInventario(i.id); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}

// --- movimentacao (com rastreabilidade de quem fez) ---
const modalMov = ref(false);
const itemMov = ref<ItemInventario | null>(null);
const historico = ref<MovimentoInventario[]>([]);
const formMov = ref({ tipo: "transferencia", destino: "", fazenda_destino_id: "", quantidade: "", observacao: "" });
const erroMov = ref("");
const salvandoMov = ref(false);

async function abrirMov(i: ItemInventario) {
  itemMov.value = i;
  formMov.value = { tipo: "transferencia", destino: "", fazenda_destino_id: "", quantidade: "", observacao: "" };
  erroMov.value = ""; modalMov.value = true;
  try { historico.value = await getMovimentosItem(i.id); } catch { historico.value = []; }
}
async function salvarMov() {
  if (!itemMov.value) return;
  const f = formMov.value;
  if (f.tipo === "transferencia" && !f.fazenda_destino_id && !f.destino.trim()) {
    erroMov.value = "Informe o destino (local ou fazenda)."; return;
  }
  salvandoMov.value = true; erroMov.value = "";
  try {
    await movimentarItem(itemMov.value.id, {
      tipo: f.tipo,
      destino: f.destino || undefined,
      fazenda_destino_id: f.fazenda_destino_id || null,
      quantidade: f.quantidade ? parseFloat(f.quantidade) : null,
      observacao: f.observacao || undefined,
    });
    modalMov.value = false; await carregar();
  } catch (e) { erroMov.value = String(e instanceof Error ? e.message : e); }
  finally { salvandoMov.value = false; }
}
</script>

<template>
  <AppShell title="Inventário" sub="Máquinas, equipamentos e onde cada coisa está" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Patrimônio</div>
      <h1>Inventário</h1>
      <p>Cadastre <b>máquinas</b> (vagão, moinho, misturador, trator), <b>equipamentos</b> (computador, barra de choque), medicações e insumos — sempre com a <b>localização</b>. Toda movimentação grava <b>quem fez</b>.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="metrics" v-if="dados">
      <KpiCard label="Itens no inventário" :value="dados.total_itens" sub="cadastrados" :icon="Boxes" tone="primary" />
      <KpiCard label="Máquinas" :value="nMaquinas" sub="vagão, trator, moinho..." :icon="Tractor" tone="blue" />
      <KpiCard label="Categorias" :value="Object.keys(dados.por_categoria).length" sub="em uso" :icon="MapPin" tone="amber" />
      <KpiCard label="Valor total" :value="brl(dados.valor_total)" sub="patrimônio" :icon="Wallet" tone="purple" />
    </div>

    <Panel title="Itens" sub="filtre por categoria ou busque por nome, série ou local" v-if="dados">
      <template #actions>
        <button class="btn btn--primary" style="height:34px" @click="abrirNovo"><Plus :size="15" /> Novo item</button>
      </template>

      <div class="filtros">
        <input class="input" v-model="busca" placeholder="Buscar por nome, nº de série ou localização..." />
        <select class="input selc" v-model="fCategoria">
          <option value="">Todas as categorias</option>
          <option v-for="c in CATEGORIAS_ITEM" :key="c.valor" :value="c.valor">{{ c.rotulo }}</option>
        </select>
      </div>

      <div class="tbl-wrap">
        <table class="tbl">
          <thead>
            <tr>
              <th>Item</th><th>Categoria</th><th>Identificação</th>
              <th>Localização</th><th class="num">Qtd</th><th class="num">Valor</th><th class="num">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="i in itensMostrados" :key="i.id">
              <td>
                <b>{{ i.nome }}</b>
                <span v-if="i.situacao !== 'ativo'" class="badge REVISAR" style="margin-left:6px"><span class="dot" />{{ i.situacao }}</span>
              </td>
              <td>{{ rotuloCat(i.categoria) }}</td>
              <td class="muted">{{ i.identificacao ?? "—" }}</td>
              <td>
                <span v-if="i.localizacao"><MapPin :size="13" /> {{ i.localizacao }}</span>
                <span v-else class="muted">—</span>
              </td>
              <td class="num tnum">{{ i.quantidade ?? "—" }} {{ i.unidade ?? "" }}</td>
              <td class="num tnum">{{ brl(i.valor) }}</td>
              <td class="num acoes">
                <button class="iconbtn" title="Movimentar" @click="abrirMov(i)"><ArrowLeftRight :size="14" /></button>
                <button class="iconbtn" title="Editar" @click="abrirEdicao(i)"><Pencil :size="14" /></button>
                <button class="iconbtn danger" title="Excluir" @click="remover(i)"><Trash2 :size="14" /></button>
              </td>
            </tr>
            <tr v-if="!itensMostrados.length">
              <td colspan="7" class="vazio">Nenhum item {{ dados.total_itens ? "com esse filtro" : "cadastrado ainda" }}.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <!-- novo/editar item -->
    <Modal v-if="modal" :titulo="editando ? 'Editar item' : 'Novo item'" sub="patrimônio da fazenda" @fechar="modal = false">
      <div class="mform">
        <div class="dupla">
          <div class="field"><label>Categoria *</label>
            <select class="input" v-model="form.categoria">
              <option v-for="c in CATEGORIAS_ITEM" :key="c.valor" :value="c.valor">{{ c.rotulo }}</option>
            </select>
          </div>
          <div class="field"><label>Situação</label>
            <select class="input" v-model="form.situacao">
              <option value="ativo">Ativo</option>
              <option value="manutencao">Em manutenção</option>
              <option value="baixado">Baixado</option>
            </select>
          </div>
        </div>
        <div class="field"><label>Nome *</label>
          <input class="input" v-model="form.nome" placeholder="ex: Vagão misturador / Computador do escritório" />
        </div>
        <div class="dupla">
          <div class="field"><label>Identificação</label>
            <input class="input" v-model="form.identificacao" placeholder="nº de série, patrimônio ou placa" />
          </div>
          <div class="field"><label>Localização</label>
            <input class="input" v-model="form.localizacao" placeholder="ex: Confinamento / Galpão 2" />
            <span class="hint">Onde o item está hoje.</span>
          </div>
        </div>
        <div class="dupla">
          <div class="field"><label>Quantidade</label>
            <input class="input tnum" type="number" v-model="form.quantidade" placeholder="ex: 1" />
          </div>
          <div class="field"><label>Unidade</label>
            <input class="input" v-model="form.unidade" placeholder="un, kg, L, sc" />
          </div>
        </div>
        <div class="dupla">
          <div class="field"><label>Valor (R$)</label>
            <input class="input tnum" type="number" v-model="form.valor" placeholder="ex: 45000" />
          </div>
          <div class="field"><label>Data de aquisição</label>
            <input class="input" type="date" v-model="form.data_aquisicao" />
          </div>
        </div>
        <div class="field"><label>Observação</label>
          <input class="input" v-model="form.observacao" />
        </div>
        <p v-if="erroModal" class="error">{{ erroModal }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modal = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvando" @click="salvar">Salvar</button>
      </template>
    </Modal>

    <!-- movimentar -->
    <Modal v-if="modalMov" titulo="Movimentar item" :sub="itemMov?.nome" @fechar="modalMov = false">
      <div class="mform">
        <div class="dupla">
          <div class="field"><label>Tipo *</label>
            <select class="input" v-model="formMov.tipo">
              <option value="transferencia">Transferência</option>
              <option value="entrada">Entrada</option>
              <option value="saida">Saída</option>
            </select>
          </div>
          <div class="field"><label>Quantidade</label>
            <input class="input tnum" type="number" v-model="formMov.quantidade" placeholder="opcional" />
          </div>
        </div>
        <div class="field" v-if="formMov.tipo === 'transferencia'">
          <label>Fazenda de destino</label>
          <select class="input" v-model="formMov.fazenda_destino_id">
            <option value="">— mesma fazenda —</option>
            <option v-for="f in fazendas" :key="f.id" :value="f.id" v-show="f.id !== fazendaId">{{ f.nome }}</option>
          </select>
          <span class="hint">Ex.: do confinamento para a Perucaba (e vice-versa).</span>
        </div>
        <div class="field"><label>Novo local</label>
          <input class="input" v-model="formMov.destino" placeholder="ex: Galpão 1 / Curral de manejo" />
        </div>
        <div class="field"><label>Observação</label>
          <input class="input" v-model="formMov.observacao" />
        </div>
        <p v-if="erroMov" class="error">{{ erroMov }}</p>

        <div v-if="historico.length" class="hist">
          <div class="hist__tit"><History :size="14" /> Histórico — quem movimentou</div>
          <div v-for="h in historico.slice(0, 6)" :key="h.id" class="hist__l">
            <span class="tnum">{{ fmtData(h.data) }}</span>
            <span class="badge OK"><span class="dot" />{{ h.tipo }}</span>
            <span>{{ h.origem ?? "—" }} → <b>{{ h.destino ?? "—" }}</b></span>
            <span class="muted">por {{ h.usuario_nome ?? "—" }}</span>
          </div>
        </div>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modalMov = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvandoMov" @click="salvarMov">Movimentar</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.selc { width: auto; min-width: 200px; appearance: auto; }
.filtros { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.filtros .input { flex: 1; min-width: 200px; }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 780px; border-collapse: collapse; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.acoes { white-space: nowrap; display: flex; gap: 4px; justify-content: flex-end; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer; display: inline-grid; place-items: center; }
.iconbtn:hover { color: var(--primary); border-color: var(--primary); }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.mform { display: flex; flex-direction: column; gap: 14px; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
.mform .hint { font-size: 12px; color: var(--muted); }
.dupla { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.hist { border-top: 1px solid var(--border); padding-top: 12px; }
.hist__tit { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em;
  color: var(--muted); display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.hist__l { display: flex; gap: 10px; align-items: center; font-size: 13px; padding: 4px 0; flex-wrap: wrap; }
@media (max-width: 700px) { .dupla { grid-template-columns: 1fr; } }
</style>
