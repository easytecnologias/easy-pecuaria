<script setup lang="ts">
import { onMounted, ref } from "vue";
import { UserPlus, Pencil, KeyRound, Trash2, Save } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import Modal from "../components/Modal.vue";
import {
  getUsuarios, criarUsuario, editarUsuario, resetarSenha, excluirUsuario,
  getOrganizacao, editarOrganizacao, getFazendas, getAuditoria, me,
  type UsuarioAdmin, type Fazenda, type AuditLog,
} from "../api";

const ROTULO_ACAO: Record<string, string> = {
  login: "Entrou no sistema", criar_usuario: "Criou usuário", editar_usuario: "Editou usuário",
  resetar_senha: "Trocou senha de usuário", excluir_usuario: "Excluiu usuário",
  editar_organizacao: "Editou organização", trocar_propria_senha: "Trocou a própria senha",
  criar_organizacao: "Criou organização", renomear_organizacao: "Renomeou organização",
};
const fmtDataHora = (s: string) => {
  const d = new Date(s);
  return d.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
};

const PAPEIS = [
  { value: "admin", label: "Administrador", desc: "Acesso total, gerencia usuários" },
  { value: "direcao", label: "Direção", desc: "Vê todas as fazendas" },
  { value: "gerente", label: "Gerente", desc: "Fazendas específicas" },
  { value: "vet", label: "Veterinário", desc: "Fazendas específicas" },
  { value: "campo", label: "Campo", desc: "Fazendas específicas" },
];
const rotuloPapel = (p: string) => PAPEIS.find((x) => x.value === p)?.label ?? p;
const veTodas = (p: string) => p === "admin" || p === "direcao";

const usuarios = ref<UsuarioAdmin[]>([]);
const fazendas = ref<Fazenda[]>([]);
const auditoria = ref<AuditLog[]>([]);
const orgNome = ref("");
const meuId = ref("");
const erro = ref("");
const acessoNegado = ref(false);

async function carregar() {
  erro.value = "";
  try {
    const [us, fz, org, eu, aud] = await Promise.all([
      getUsuarios(), getFazendas(), getOrganizacao(), me(), getAuditoria(),
    ]);
    usuarios.value = us; fazendas.value = fz; orgNome.value = org.nome; meuId.value = eu.id;
    auditoria.value = aud;
  } catch (e) {
    const msg = String(e instanceof Error ? e.message : e);
    if (msg.includes("administrador") || msg.includes("403")) acessoNegado.value = true;
    else erro.value = msg;
  }
}
onMounted(carregar);

const salvandoOrg = ref(false);
async function salvarOrg() {
  if (!orgNome.value.trim()) return;
  salvandoOrg.value = true;
  try { await editarOrganizacao(orgNome.value.trim()); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
  finally { salvandoOrg.value = false; }
}

const modal = ref(false);
const editId = ref<string | null>(null);
const form = ref({ nome: "", email: "", senha: "", papel: "gerente", fazenda_ids: [] as string[] });
const erroModal = ref("");
const salvando = ref(false);
function abrirNovo() {
  editId.value = null;
  form.value = { nome: "", email: "", senha: "", papel: "gerente", fazenda_ids: [] };
  erroModal.value = ""; modal.value = true;
}
function abrirEdicao(u: UsuarioAdmin) {
  editId.value = u.id;
  form.value = { nome: u.nome, email: u.email, senha: "", papel: u.papel, fazenda_ids: [...u.fazenda_ids] };
  erroModal.value = ""; modal.value = true;
}
function toggleFazenda(id: string) {
  const i = form.value.fazenda_ids.indexOf(id);
  if (i >= 0) form.value.fazenda_ids.splice(i, 1);
  else form.value.fazenda_ids.push(id);
}
async function salvarUsuario() {
  if (!form.value.nome.trim()) { erroModal.value = "Informe o nome."; return; }
  if (!editId.value && (!form.value.email.trim() || !form.value.email.includes("@"))) {
    erroModal.value = "Informe um email válido."; return;
  }
  if (!editId.value && form.value.senha.length < 6) { erroModal.value = "A senha deve ter ao menos 6 caracteres."; return; }
  salvando.value = true; erroModal.value = "";
  try {
    const fids = veTodas(form.value.papel) ? [] : form.value.fazenda_ids;
    if (editId.value) {
      await editarUsuario(editId.value, { nome: form.value.nome.trim(), papel: form.value.papel, fazenda_ids: fids });
    } else {
      await criarUsuario({
        nome: form.value.nome.trim(), email: form.value.email.trim(),
        senha: form.value.senha, papel: form.value.papel, fazenda_ids: fids,
      });
    }
    modal.value = false; await carregar();
  } catch (e) { erroModal.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}

const modalSenha = ref(false);
const senhaAlvo = ref<UsuarioAdmin | null>(null);
const novaSenha = ref("");
const erroSenha = ref("");
const salvandoSenha = ref(false);
function abrirSenha(u: UsuarioAdmin) { senhaAlvo.value = u; novaSenha.value = ""; erroSenha.value = ""; modalSenha.value = true; }
async function salvarSenha() {
  if (novaSenha.value.length < 6) { erroSenha.value = "A senha deve ter ao menos 6 caracteres."; return; }
  salvandoSenha.value = true; erroSenha.value = "";
  try { await resetarSenha(senhaAlvo.value!.id, novaSenha.value); modalSenha.value = false; }
  catch (e) { erroSenha.value = String(e instanceof Error ? e.message : e); }
  finally { salvandoSenha.value = false; }
}

async function alternarAtivo(u: UsuarioAdmin) {
  try { await editarUsuario(u.id, { ativo: !u.ativo }); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function remover(u: UsuarioAdmin) {
  if (!confirm(`Excluir o usuário ${u.nome} (${u.email})? Esta ação não pode ser desfeita.`)) return;
  try { await excluirUsuario(u.id); await carregar(); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}

const escopoLabel = (u: UsuarioAdmin) =>
  veTodas(u.papel) ? "Todas" : (u.fazenda_ids.length ? `${u.fazenda_ids.length} fazenda(s)` : "Nenhuma");
</script>

<template>
  <AppShell title="Administração" sub="Usuários e configurações" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Administração</div>
      <h1>Usuários e organização</h1>
      <p>Crie e gerencie os acessos ao sistema: defina o <b>papel</b> de cada pessoa e a quais <b>fazendas</b> ela tem acesso. Só administradores entram aqui.</p>
    </div>

    <div v-if="acessoNegado" class="negado">
      🔒 Acesso restrito a administradores.
    </div>

    <template v-else>
      <p v-if="erro" class="error">{{ erro }}</p>

      <Panel title="Organização" sub="dados do grupo">
        <div class="orgrow">
          <div class="field" style="flex:1">
            <label>Nome do grupo</label>
            <input class="input" v-model="orgNome" placeholder="ex: Grupo JLN" @keyup.enter="salvarOrg" />
          </div>
          <button class="btn btn--primary" style="height:40px" :disabled="salvandoOrg" @click="salvarOrg">
            <Save :size="15" /> Salvar
          </button>
        </div>
      </Panel>

      <Panel title="Usuários" sub="acessos ao sistema" style="margin-top:16px">
        <template #actions>
          <button class="btn btn--primary" style="height:34px" @click="abrirNovo"><UserPlus :size="15" /> Novo usuário</button>
        </template>
        <div class="tbl-wrap">
          <table class="tbl">
            <colgroup><col style="width:22%"/><col style="width:24%"/><col style="width:16%"/><col style="width:14%"/><col style="width:10%"/><col style="width:14%"/></colgroup>
            <thead><tr><th>Nome</th><th>Email</th><th>Papel</th><th>Fazendas</th><th>Status</th><th class="num">Ações</th></tr></thead>
            <tbody>
              <tr v-for="u in usuarios" :key="u.id" :class="{ inativo: !u.ativo }">
                <td><strong>{{ u.nome }}</strong><span v-if="u.id === meuId" class="voce">você</span></td>
                <td class="muted">{{ u.email }}</td>
                <td><span :class="['badge', u.papel === 'admin' ? 'OK' : 'REVISAR']"><span class="dot" /> {{ rotuloPapel(u.papel) }}</span></td>
                <td class="muted">{{ escopoLabel(u) }}</td>
                <td>
                  <button class="statusbtn" :class="u.ativo ? 'on' : 'off'" @click="alternarAtivo(u)"
                          :disabled="u.id === meuId" :title="u.id === meuId ? 'Não pode desativar a si mesmo' : 'Ativar/desativar'">
                    {{ u.ativo ? "Ativo" : "Inativo" }}
                  </button>
                </td>
                <td class="num acoes">
                  <button class="iconbtn" title="Editar" @click="abrirEdicao(u)"><Pencil :size="15" /></button>
                  <button class="iconbtn" title="Trocar senha" @click="abrirSenha(u)"><KeyRound :size="15" /></button>
                  <button class="iconbtn danger" title="Excluir" :disabled="u.id === meuId" @click="remover(u)"><Trash2 :size="15" /></button>
                </td>
              </tr>
              <tr v-if="!usuarios.length"><td colspan="6" class="vazio">Nenhum usuário.</td></tr>
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Auditoria" sub="ações recentes no sistema — quem fez o quê" style="margin-top:16px">
        <div class="tbl-wrap">
          <table class="tbl">
            <colgroup><col style="width:16%"/><col style="width:26%"/><col style="width:24%"/><col style="width:34%"/></colgroup>
            <thead><tr><th>Quando</th><th>Usuário</th><th>Ação</th><th>Detalhe</th></tr></thead>
            <tbody>
              <tr v-for="a in auditoria" :key="a.id">
                <td class="muted">{{ fmtDataHora(a.created_at) }}</td>
                <td>{{ a.usuario_email }}</td>
                <td><span class="badge REVISAR"><span class="dot" /> {{ ROTULO_ACAO[a.acao] ?? a.acao }}</span></td>
                <td class="muted">{{ a.detalhe ?? "—" }}</td>
              </tr>
              <tr v-if="!auditoria.length"><td colspan="4" class="vazio">Nenhuma ação registrada ainda.</td></tr>
            </tbody>
          </table>
        </div>
      </Panel>
    </template>

    <!-- Modal criar/editar usuário -->
    <Modal v-if="modal" :titulo="editId ? 'Editar usuário' : 'Novo usuário'"
           :sub="editId ? 'papel e permissões' : 'crie um acesso ao sistema'" :largura="560" @fechar="modal = false">
      <div class="mform">
        <div class="field"><label>Nome *</label><input class="input" v-model="form.nome" placeholder="ex: João da Silva" /></div>
        <div class="field" v-if="!editId"><label>Email *</label><input class="input" v-model="form.email" placeholder="ex: joao@fazenda.com" /></div>
        <div class="field" v-else><label>Email</label><input class="input" :value="form.email" disabled /></div>
        <div class="field" v-if="!editId"><label>Senha *</label><input class="input" type="text" v-model="form.senha" placeholder="mín. 6 caracteres" /></div>
        <div class="field"><label>Papel</label>
          <select class="input selc" v-model="form.papel">
            <option v-for="p in PAPEIS" :key="p.value" :value="p.value">{{ p.label }} — {{ p.desc }}</option>
          </select>
        </div>
        <div class="field" v-if="!veTodas(form.papel)">
          <label>Fazendas com acesso</label>
          <div class="fzlist">
            <label v-for="f in fazendas" :key="f.id" class="fzitem">
              <input type="checkbox" :checked="form.fazenda_ids.includes(f.id)" @change="toggleFazenda(f.id)" />
              {{ f.nome }}
            </label>
            <p v-if="!fazendas.length" class="muted" style="font-size:13px">Nenhuma fazenda cadastrada.</p>
          </div>
        </div>
        <p v-else class="hint">Administrador e Direção enxergam <b>todas as fazendas</b> automaticamente.</p>
        <p v-if="erroModal" class="error">{{ erroModal }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modal = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvando" @click="salvarUsuario">{{ editId ? "Salvar" : "Criar usuário" }}</button>
      </template>
    </Modal>

    <!-- Modal senha -->
    <Modal v-if="modalSenha" titulo="Trocar senha" :sub="senhaAlvo?.email" :largura="440" @fechar="modalSenha = false">
      <div class="mform">
        <div class="field"><label>Nova senha *</label>
          <input class="input" type="text" v-model="novaSenha" placeholder="mín. 6 caracteres" @keyup.enter="salvarSenha" />
          <span class="hint">A senha é definida por você e informada ao usuário.</span>
        </div>
        <p v-if="erroSenha" class="error">{{ erroSenha }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modalSenha = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvandoSenha" @click="salvarSenha">Salvar senha</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.negado { background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 40px; text-align: center; color: var(--muted); font-size: 15px; }
.orgrow { display: flex; gap: 12px; align-items: flex-end; }
.field { display: grid; gap: 6px; }
.field label { font-size: 13px; font-weight: 600; }
.selc { appearance: auto; }
.tbl-wrap { overflow-x: auto; }
.tbl { width: 100%; min-width: 640px; border-collapse: collapse; table-layout: fixed; }
.tbl th, .tbl td { padding: 11px 12px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.tbl .num { text-align: right; }
.tbl tr.inativo td { opacity: .55; }
.voce { font-size: 11px; background: #eef2f4; color: var(--muted); border-radius: 999px; padding: 1px 7px; margin-left: 7px; }
.vazio { text-align: center; padding: 20px; color: var(--muted); }
.statusbtn { border: 1px solid var(--border); background: var(--surface); border-radius: 999px;
  padding: 3px 12px; font-size: 12.5px; font-weight: 600; cursor: pointer; }
.statusbtn.on { color: var(--primary); border-color: #bfe0d0; background: #f2f8f5; }
.statusbtn.off { color: var(--muted); }
.statusbtn:disabled { cursor: not-allowed; opacity: .6; }
.acoes { white-space: nowrap; }
.iconbtn { border: 1px solid var(--border); background: var(--surface); color: var(--muted);
  width: 30px; height: 30px; border-radius: 7px; cursor: pointer; display: inline-grid; place-items: center; margin-left: 6px; }
.iconbtn:hover { background: #f2f8f5; color: var(--primary); border-color: #bfe0d0; }
.iconbtn.danger:hover { background: #fcebeb; color: var(--danger); border-color: #f0c9c9; }
.iconbtn:disabled { cursor: not-allowed; opacity: .4; }
.iconbtn:disabled:hover { background: var(--surface); color: var(--muted); border-color: var(--border); }
.mform { display: flex; flex-direction: column; gap: 13px; }
.fzlist { display: flex; flex-direction: column; gap: 8px; border: 1px solid var(--border); border-radius: 8px; padding: 12px; max-height: 190px; overflow-y: auto; }
.fzitem { display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; }
.hint { font-size: 12px; color: var(--muted); }
</style>
