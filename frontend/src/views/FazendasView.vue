<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Plus, Pencil, Trash2, MapPin } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, criarFazenda, atualizarFazenda, excluirFazenda, type Fazenda,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const erro = ref("");

const modalAberto = ref(false);
const editando = ref<Fazenda | null>(null);
const form = ref({ nome: "", municipio: "", uf: "" });
const erroModal = ref("");
const salvando = ref(false);

async function carregar() {
  erro.value = "";
  try { fazendas.value = await getFazendas(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}

function abrirNova() {
  editando.value = null;
  form.value = { nome: "", municipio: "", uf: "" };
  erroModal.value = ""; modalAberto.value = true;
}
function abrirEdicao(f: Fazenda) {
  editando.value = f;
  form.value = { nome: f.nome, municipio: f.municipio ?? "", uf: f.uf ?? "" };
  erroModal.value = ""; modalAberto.value = true;
}
async function salvar() {
  if (!form.value.nome.trim()) { erroModal.value = "Dê um nome à fazenda."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    if (editando.value) await atualizarFazenda(editando.value.id, { ...form.value });
    else await criarFazenda({ ...form.value });
    modalAberto.value = false;
    await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
async function remover(f: Fazenda) {
  if (!confirm(`Excluir a fazenda "${f.nome}"? Isso apaga também as metas dela. Não pode ser desfeito.`)) return;
  erro.value = "";
  try { await excluirFazenda(f.id); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}

onMounted(carregar);
</script>

<template>
  <AppShell title="Fazendas" sub="Unidades do grupo" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Unidades</div>
      <h1>Fazendas do grupo</h1>
      <p>Cadastre e gerencie as fazendas. Cada fazenda nova já vem com as metas padrão — depois é só ajustar em <b>Metas</b>.</p>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <Panel title="Fazendas" :sub="`${fazendas.length} no grupo`">
      <template #actions>
        <button class="btn btn--primary" style="height:36px" @click="abrirNova"><Plus :size="15" /> Nova fazenda</button>
      </template>
      <div class="tbl-wrap">
        <table class="ftbl">
          <colgroup><col style="width:48%" /><col style="width:34%" /><col style="width:18%" /></colgroup>
          <thead><tr><th>Fazenda</th><th>Local</th><th class="num">Ações</th></tr></thead>
          <tbody>
            <tr v-for="f in fazendas" :key="f.id">
              <td><strong>{{ f.nome }}</strong></td>
              <td class="muted">
                <span class="row" style="gap:5px" v-if="f.municipio || f.uf"><MapPin :size="14" /> {{ f.municipio }}{{ f.uf ? "/" + f.uf : "" }}</span>
                <span v-else>—</span>
              </td>
              <td class="num acoes">
                <button class="iconbtn" title="Editar" @click="abrirEdicao(f)"><Pencil :size="15" /></button>
                <button class="iconbtn danger" title="Excluir" @click="remover(f)"><Trash2 :size="15" /></button>
              </td>
            </tr>
            <tr v-if="!fazendas.length"><td colspan="3" class="vazio">Nenhuma fazenda cadastrada.</td></tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <Modal v-if="modalAberto" :titulo="editando ? 'Editar fazenda' : 'Nova fazenda'"
           sub="uma unidade do grupo" @fechar="modalAberto = false">
      <div class="mform">
        <div class="field"><label>Nome *</label>
          <input class="input" v-model="form.nome" placeholder="ex: Fazenda Boa Vista" @keyup.enter="salvar" />
        </div>
        <div class="two">
          <div class="field"><label>Município</label>
            <input class="input" v-model="form.municipio" placeholder="ex: Arapiraca" />
          </div>
          <div class="field"><label>UF</label>
            <input class="input" v-model="form.uf" maxlength="2" placeholder="AL" />
          </div>
        </div>
        <p v-if="erroModal" class="error">{{ erroModal }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modalAberto = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvando" @click="salvar">{{ editando ? "Salvar" : "Criar fazenda" }}</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.tbl-wrap { overflow-x: auto; }
.ftbl { width: 100%; min-width: 420px; border-collapse: collapse; table-layout: fixed; }
.ftbl th, .ftbl td { padding: 13px 14px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.ftbl tbody tr:last-child td { border-bottom: none; }
.ftbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.ftbl .num { text-align: right; }
.acoes { white-space: nowrap; }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 32px; height: 32px; border-radius: 7px; cursor: pointer; display: inline-grid; place-items: center; margin-left: 6px; }
.iconbtn:hover { background: #f2f8f5; color: var(--primary); border-color: #bfe0d0; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.vazio { text-align: center; padding: 22px; color: var(--muted); }
.mform { display: flex; flex-direction: column; gap: 14px; }
.mform .two { display: grid; grid-template-columns: 2fr 1fr; gap: 12px; align-items: start; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
</style>
