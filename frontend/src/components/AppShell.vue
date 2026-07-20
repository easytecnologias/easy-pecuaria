<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { LogOut, RefreshCw, Plus, Menu, KeyRound } from "lucide-vue-next";
import { clearToken, getMeCached, trocarMinhaSenha, refreshTokenThrottled } from "../api";
import Modal from "./Modal.vue";

defineProps<{ title: string; sub?: string }>();
const emit = defineEmits<{ refresh: [] }>();

const route = useRoute();
const router = useRouter();

const menuAberto = ref(false);
watch(() => route.fullPath, () => { menuAberto.value = false; });

// papel do usuário logado — para exibir itens só de administrador
const papel = ref("");
const superadmin = ref(false);
const ehAdmin = computed(() => papel.value === "admin" || papel.value === "direcao");
onMounted(async () => {
  try { const u = await getMeCached(); papel.value = u.papel; superadmin.value = !!u.is_superadmin; }
  catch { /* ignora */ }
  refreshTokenThrottled().catch(() => { /* sessão desliza silenciosamente */ });
});

// troca da própria senha (auto-serviço)
const modalSenha = ref(false);
const fs = ref({ atual: "", nova: "", conf: "" });
const erroSenha = ref("");
const okSenha = ref(false);
const salvandoSenha = ref(false);
function abrirSenha() { fs.value = { atual: "", nova: "", conf: "" }; erroSenha.value = ""; okSenha.value = false; modalSenha.value = true; }
async function salvarSenha() {
  if (fs.value.nova.length < 6) { erroSenha.value = "A nova senha deve ter ao menos 6 caracteres."; return; }
  if (fs.value.nova !== fs.value.conf) { erroSenha.value = "A confirmação não confere."; return; }
  salvandoSenha.value = true; erroSenha.value = "";
  try {
    await trocarMinhaSenha(fs.value.atual, fs.value.nova);
    okSenha.value = true;
  } catch (e) { erroSenha.value = String(e instanceof Error ? e.message : e); }
  finally { salvandoSenha.value = false; }
}

// menu agrupado por propósito — cada categoria com sua função clara
const grupos = [
  {
    titulo: "Início",
    itens: [
      { to: "/painel", label: "Painel", emoji: "📊", match: ["/painel"] },
      { to: "/alertas", label: "Alertas", emoji: "🔔" },
      { to: "/relatorios", label: "Relatórios", emoji: "📄" },
    ],
  },
  {
    titulo: "Rebanho",
    itens: [
      { to: "/rebanho", label: "Rebanho", emoji: "🐂", match: ["/rebanho", "/animais"] },
      { to: "/campo", label: "Modo campo (pesar)", emoji: "📴" },
      { to: "/registrar", label: "Registrar dados", emoji: "⚖️" },
      { to: "/movimentacao", label: "Movimentação", emoji: "↔️" },
    ],
  },
  {
    titulo: "Reprodução",
    itens: [
      { to: "/reproducao", label: "Reprodução", emoji: "🧬" },
      { to: "/partos", label: "Partos", emoji: "🐣" },
      { to: "/desmame", label: "Desmame", emoji: "🍼" },
    ],
  },
  {
    titulo: "Saúde",
    itens: [
      { to: "/sanitario", label: "Sanitário", emoji: "💉" },
      { to: "/escore", label: "Escore corporal", emoji: "📏" },
    ],
  },
  {
    titulo: "Nutrição",
    itens: [
      { to: "/nutricao", label: "Nutrição", emoji: "🥗" },
      { to: "/estoque", label: "Estoque", emoji: "🌽" },
    ],
  },
  {
    titulo: "Financeiro",
    itens: [
      { to: "/financeiro", label: "Financeiro", emoji: "💵" },
      { to: "/mercado", label: "Mercado", emoji: "💰" },
    ],
  },
  {
    titulo: "Ajustes",
    itens: [
      { to: "/fazendas", label: "Fazendas", emoji: "🏡", match: ["/fazendas"] },
      { to: "/inventario", label: "Inventário", emoji: "📦" },
      { to: "/metas", label: "Metas", emoji: "🎯" },
      { to: "/admin", label: "Administração", emoji: "⚙️", adminOnly: true },
    ],
  },
  {
    titulo: "Plataforma",
    itens: [
      { to: "/plataforma", label: "Organizações", emoji: "🏢", superadminOnly: true },
    ],
  },
];

// esconde itens conforme o papel/super-admin do usuário
function podeVer(i: Record<string, unknown>) {
  if (i.superadminOnly) return superadmin.value;
  if (i.adminOnly) return ehAdmin.value;
  return true;
}
const gruposVisiveis = computed(() =>
  grupos
    .map((g) => ({ ...g, itens: g.itens.filter(podeVer) }))
    .filter((g) => g.itens.length)
);

function ativo(item: { to: string; match?: string[] }) {
  if (route.path === item.to) return true;
  return (item.match ?? []).some((m) => route.path.startsWith(m));
}

function sair() {
  clearToken();
  router.push("/login");
}
</script>

<template>
  <div class="app-shell">
    <div class="sidebar-backdrop" v-if="menuAberto" @click="menuAberto = false" />
    <aside class="sidebar" :class="{ 'sidebar--open': menuAberto }">
      <div class="sidebar__brand">
        <div class="sidebar__logo">JLN</div>
        <div>
          <div class="sidebar__title">Pecuária</div>
          <div class="sidebar__sub">Grupo JLN</div>
        </div>
      </div>
      <nav class="nav">
        <template v-for="g in gruposVisiveis" :key="g.titulo">
          <div class="nav__group">{{ g.titulo }}</div>
          <RouterLink
            v-for="item in g.itens"
            :key="item.to"
            :to="item.to"
            class="nav__item"
            :class="{ active: ativo(item) }"
          >
            <span class="nav__emoji">{{ item.emoji }}</span>
            {{ item.label }}
          </RouterLink>
        </template>
      </nav>
      <div class="sidebar__footer">
        <RouterLink to="/ajuda" class="nav__item" :class="{ active: route.path === '/ajuda' }">
          <span class="nav__emoji">🧭</span> Como funciona
        </RouterLink>
        <div class="nav__item" @click="abrirSenha">
          <KeyRound :size="18" /> Trocar senha
        </div>
        <div class="nav__item" @click="sair">
          <LogOut :size="18" /> Sair
        </div>
      </div>
    </aside>

    <main class="main-area">
      <header class="topbar">
        <div class="row" style="gap:12px;min-width:0">
          <button class="hamburger" @click="menuAberto = !menuAberto" aria-label="Menu">
            <Menu :size="20" />
          </button>
          <div class="topbar__logo">JLN</div>
          <div style="min-width:0">
            <div class="topbar__title">{{ title }}</div>
            <div class="topbar__sub" v-if="sub">{{ sub }}</div>
          </div>
        </div>
        <div class="topbar__actions">
          <button class="btn btn--secondary" @click="emit('refresh')">
            <RefreshCw :size="16" /> <span>Atualizar</span>
          </button>
          <RouterLink to="/registrar" class="btn btn--primary reg-desktop">
            <Plus :size="16" /> <span>Registrar</span>
          </RouterLink>
        </div>
      </header>
      <section class="workspace">
        <slot />
      </section>
    </main>

    <!-- barra de abas (só no celular) — substitui o menu lateral -->
    <nav class="mtabs">
      <RouterLink to="/painel" class="mtab" :class="{ on: ativo({ to: '/painel', match: ['/painel'] }) }"><span class="mi">📊</span>Painel</RouterLink>
      <RouterLink to="/rebanho" class="mtab" :class="{ on: ativo({ to: '/rebanho', match: ['/rebanho', '/animais'] }) }"><span class="mi">🐂</span>Rebanho</RouterLink>
      <RouterLink to="/campo" class="mfab" aria-label="Pesar no campo">+</RouterLink>
      <RouterLink to="/relatorios" class="mtab" :class="{ on: ativo({ to: '/relatorios' }) }"><span class="mi">📄</span>Relatórios</RouterLink>
      <button class="mtab" type="button" @click="menuAberto = true"><span class="mi">☰</span>Menu</button>
    </nav>

    <Modal v-if="modalSenha" titulo="Trocar minha senha" sub="auto-serviço" :largura="440" @fechar="modalSenha = false">
      <div v-if="okSenha" class="senha-ok">✅ Senha alterada com sucesso.</div>
      <div v-else class="senha-form">
        <div class="sfield"><label>Senha atual *</label><input class="input" type="password" v-model="fs.atual" /></div>
        <div class="sfield"><label>Nova senha *</label><input class="input" type="password" v-model="fs.nova" placeholder="mín. 6 caracteres" /></div>
        <div class="sfield"><label>Confirmar nova senha *</label><input class="input" type="password" v-model="fs.conf" @keyup.enter="salvarSenha" /></div>
        <p v-if="erroSenha" class="error">{{ erroSenha }}</p>
      </div>
      <template #acoes>
        <button v-if="okSenha" class="btn btn--primary" @click="modalSenha = false">Fechar</button>
        <template v-else>
          <button class="btn btn--secondary" @click="modalSenha = false">Cancelar</button>
          <button class="btn btn--primary" :disabled="salvandoSenha" @click="salvarSenha">Salvar</button>
        </template>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.nav__emoji { width: 20px; text-align: center; font-size: 16px; line-height: 1; }
.senha-form { display: flex; flex-direction: column; gap: 13px; }
.sfield { display: grid; gap: 6px; }
.sfield label { font-size: 13px; font-weight: 600; }
.senha-ok { padding: 14px 4px; font-size: 15px; color: var(--primary); font-weight: 600; }
</style>
