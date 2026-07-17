<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { LogOut, RefreshCw, Plus, Menu } from "lucide-vue-next";
import { clearToken, me } from "../api";

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
  try { const u = await me(); papel.value = u.papel; superadmin.value = !!u.is_superadmin; }
  catch { /* ignora */ }
});

// menu agrupado por propósito — cada categoria com sua função clara
const grupos = [
  {
    titulo: "Início",
    itens: [
      { to: "/painel", label: "Painel", emoji: "📊", match: ["/painel"] },
      { to: "/alertas", label: "Alertas", emoji: "🔔" },
    ],
  },
  {
    titulo: "Rebanho",
    itens: [
      { to: "/rebanho", label: "Rebanho", emoji: "🐂", match: ["/rebanho", "/animais"] },
      { to: "/registrar", label: "Registrar dados", emoji: "⚖️" },
      { to: "/movimentacao", label: "Movimentação", emoji: "↔️" },
    ],
  },
  {
    titulo: "Reprodução",
    itens: [
      { to: "/reproducao", label: "Reprodução", emoji: "🧬" },
      { to: "/partos", label: "Partos", emoji: "🐣" },
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
          <div style="min-width:0">
            <div class="topbar__title">{{ title }}</div>
            <div class="topbar__sub" v-if="sub">{{ sub }}</div>
          </div>
        </div>
        <div class="topbar__actions">
          <button class="btn btn--secondary" @click="emit('refresh')">
            <RefreshCw :size="16" /> Atualizar
          </button>
          <RouterLink to="/registrar" class="btn btn--primary">
            <Plus :size="16" /> Registrar
          </RouterLink>
        </div>
      </header>
      <section class="workspace">
        <slot />
      </section>
    </main>
  </div>
</template>

<style scoped>
.nav__emoji { width: 20px; text-align: center; font-size: 16px; line-height: 1; }
</style>
