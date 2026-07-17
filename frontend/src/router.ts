import { createRouter, createWebHistory } from "vue-router";
import { getToken } from "./api";

const routes = [
  { path: "/login", component: () => import("./views/LoginView.vue"), meta: { publico: true } },
  { path: "/", redirect: "/painel" },
  { path: "/rebanho", component: () => import("./views/RebanhoView.vue") },
  { path: "/animais/:id", component: () => import("./views/FichaAnimalView.vue") },
  { path: "/registrar", component: () => import("./views/RegistrarView.vue") },
  { path: "/campo", component: () => import("./views/CampoView.vue") },
  { path: "/reproducao", component: () => import("./views/ReproducaoView.vue") },
  { path: "/partos", component: () => import("./views/PartosView.vue") },
  { path: "/escore", component: () => import("./views/EscoreView.vue") },
  { path: "/nutricao", component: () => import("./views/NutricaoView.vue") },
  { path: "/estoque", component: () => import("./views/EstoqueView.vue") },
  { path: "/sanitario", component: () => import("./views/SanitarioView.vue") },
  { path: "/movimentacao", component: () => import("./views/MovimentacaoView.vue") },
  { path: "/painel", component: () => import("./views/DashboardView.vue") },
  { path: "/alertas", component: () => import("./views/AlertasView.vue") },
  { path: "/relatorios", component: () => import("./views/RelatoriosView.vue") },
  { path: "/mercado", component: () => import("./views/MercadoView.vue") },
  { path: "/financeiro", component: () => import("./views/FinanceiroView.vue") },
  { path: "/metas", component: () => import("./views/MetasView.vue") },
  { path: "/admin", component: () => import("./views/AdministracaoView.vue") },
  { path: "/plataforma", component: () => import("./views/PlataformaView.vue") },
  { path: "/ajuda", component: () => import("./views/AjudaView.vue") },
  { path: "/fazendas", component: () => import("./views/FazendasView.vue") },
  { path: "/fazendas/:id", component: () => import("./views/FazendaDetailView.vue") },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  if (!to.meta.publico && !getToken()) return "/login";
  if (to.path === "/login" && getToken()) return "/painel";
});

export default router;
