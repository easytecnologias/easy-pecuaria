<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Building2, Plus, Warehouse, Users } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import KpiCard from "../components/KpiCard.vue";
import Modal from "../components/Modal.vue";
import { getOrganizacoes, criarOrganizacao, type OrgPlataforma } from "../api";

const orgs = ref<OrgPlataforma[]>([]);
const erro = ref("");
const acessoNegado = ref(false);

const totalFazendas = computed(() => orgs.value.reduce((s, o) => s + o.n_fazendas, 0));
const totalUsuarios = computed(() => orgs.value.reduce((s, o) => s + o.n_usuarios, 0));

async function carregar() {
  erro.value = "";
  try { orgs.value = await getOrganizacoes(); }
  catch (e) {
    const msg = String(e instanceof Error ? e.message : e);
    if (msg.includes("super-admin") || msg.includes("403")) acessoNegado.value = true;
    else erro.value = msg;
  }
}
onMounted(carregar);

const modal = ref(false);
const form = ref({ nome: "", slug: "", admin_nome: "", admin_email: "", admin_senha: "" });
const slugTocado = ref(false);
const erroModal = ref("");
const salvando = ref(false);
const criada = ref<{ org: string; email: string; senha: string } | null>(null);

function slugify(t: string) { return t.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }
function onNome() { if (!slugTocado.value) form.value.slug = slugify(form.value.nome); }

function abrir() {
  form.value = { nome: "", slug: "", admin_nome: "", admin_email: "", admin_senha: "" };
  slugTocado.value = false; erroModal.value = ""; criada.value = null; modal.value = true;
}
async function salvar() {
  if (!form.value.nome.trim()) { erroModal.value = "Informe o nome da organização."; return; }
  if (!form.value.admin_nome.trim()) { erroModal.value = "Informe o nome do admin."; return; }
  if (!form.value.admin_email.includes("@")) { erroModal.value = "Email do admin inválido."; return; }
  if (form.value.admin_senha.length < 6) { erroModal.value = "A senha deve ter ao menos 6 caracteres."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    await criarOrganizacao({
      nome: form.value.nome.trim(), slug: form.value.slug || slugify(form.value.nome),
      admin_nome: form.value.admin_nome.trim(), admin_email: form.value.admin_email.trim(),
      admin_senha: form.value.admin_senha,
    });
    criada.value = { org: form.value.nome.trim(), email: form.value.admin_email.trim(), senha: form.value.admin_senha };
    await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
</script>

<template>
  <AppShell title="Plataforma" sub="Organizações (clientes)" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Super-admin</div>
      <h1>Organizações da plataforma</h1>
      <p>Cada organização é um <b>cliente independente</b>, com seus próprios usuários, fazendas e dados — totalmente isolados dos demais. Aqui você faz o <b>onboarding</b> de novos clientes.</p>
    </div>

    <div v-if="acessoNegado" class="negado">🔒 Acesso restrito ao super-admin da plataforma.</div>

    <template v-else>
      <p v-if="erro" class="error">{{ erro }}</p>

      <div class="metrics">
        <KpiCard label="Organizações" :value="orgs.length" sub="clientes" :icon="Building2" tone="primary" />
        <KpiCard label="Fazendas" :value="totalFazendas" sub="na plataforma" :icon="Warehouse" tone="blue" />
        <KpiCard label="Usuários" :value="totalUsuarios" sub="na plataforma" :icon="Users" tone="amber" />
      </div>

      <Panel title="Organizações" sub="cada linha é um cliente isolado">
        <template #actions>
          <button class="btn btn--primary" style="height:34px" @click="abrir"><Plus :size="15" /> Nova organização</button>
        </template>
        <div class="tbl-wrap">
          <table class="tbl">
            <colgroup><col style="width:40%"/><col style="width:28%"/><col style="width:16%"/><col style="width:16%"/></colgroup>
            <thead><tr><th>Organização</th><th>Slug</th><th class="num">Fazendas</th><th class="num">Usuários</th></tr></thead>
            <tbody>
              <tr v-for="o in orgs" :key="o.id">
                <td><strong>{{ o.nome }}</strong></td>
                <td class="muted">{{ o.slug }}</td>
                <td class="num tnum">{{ o.n_fazendas }}</td>
                <td class="num tnum">{{ o.n_usuarios }}</td>
              </tr>
              <tr v-if="!orgs.length"><td colspan="4" class="vazio">Nenhuma organização.</td></tr>
            </tbody>
          </table>
        </div>
      </Panel>
    </template>

    <Modal v-if="modal" titulo="Nova organização" sub="cria o cliente + o primeiro admin dele" :largura="560" @fechar="modal = false">
      <div v-if="criada" class="ok-box">
        <div class="ok-title">✅ Organização "{{ criada.org }}" criada!</div>
        <p>O acesso do administrador dela:</p>
        <div class="cred"><span>Email</span><b>{{ criada.email }}</b></div>
        <div class="cred"><span>Senha</span><b>{{ criada.senha }}</b></div>
        <p class="hint">Passe essas credenciais ao cliente. Ele entra e monta as próprias fazendas e usuários — isolado dos demais.</p>
      </div>
      <div v-else class="mform">
        <div class="two">
          <div class="field"><label>Nome da organização *</label>
            <input class="input" v-model="form.nome" @input="onNome" placeholder="ex: Fazendas Boa Vista" />
          </div>
          <div class="field"><label>Slug (identificador)</label>
            <input class="input" v-model="form.slug" @input="slugTocado = true" placeholder="ex: boa-vista" />
          </div>
        </div>
        <div class="sep">Administrador inicial do cliente</div>
        <div class="field"><label>Nome do admin *</label><input class="input" v-model="form.admin_nome" placeholder="ex: Maria Souza" /></div>
        <div class="two">
          <div class="field"><label>Email *</label><input class="input" v-model="form.admin_email" placeholder="ex: maria@boavista.com" /></div>
          <div class="field"><label>Senha *</label><input class="input" type="text" v-model="form.admin_senha" placeholder="mín. 6 caracteres" /></div>
        </div>
        <p v-if="erroModal" class="error">{{ erroModal }}</p>
      </div>
      <template #acoes>
        <button v-if="criada" class="btn btn--primary" @click="modal = false">Concluir</button>
        <template v-else>
          <button class="btn btn--secondary" @click="modal = false">Cancelar</button>
          <button class="btn btn--primary" :disabled="salvando" @click="salvar">Criar organização</button>
        </template>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.negado { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 40px; text-align: center; color: var(--muted); font-size: 15px; }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 520px; border-collapse: collapse; table-layout: fixed; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.mform { display: flex; flex-direction: column; gap: 13px; }
.mform .two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
.mform .field { display: grid; gap: 6px; }
.mform .field label { font-size: 13px; font-weight: 600; }
.sep { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 700; margin-top: 4px; padding-top: 10px; border-top: 1px solid var(--border); }
.ok-box { display: flex; flex-direction: column; gap: 10px; }
.ok-title { font-size: 16px; font-weight: 700; color: var(--primary); }
.cred { display: flex; justify-content: space-between; background: #f3f5f7; border-radius: 8px; padding: 10px 14px; }
.cred span { color: var(--muted); font-size: 13px; }
.hint { font-size: 12.5px; color: var(--muted); }
</style>
