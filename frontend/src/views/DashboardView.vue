<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Warehouse, TriangleAlert, CircleCheck, Search } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import KpiCard from "../components/KpiCard.vue";
import Panel from "../components/Panel.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { getDashboard, getEvolucaoRebanho, fmtValor, type Dashboard, type EvolucaoRebanho } from "../api";

const router = useRouter();
const data = ref<Dashboard | null>(null);
const evolucao = ref<EvolucaoRebanho | null>(null);
const erro = ref("");
const carregando = ref(false);

function sev(d: Dashboard | null, k: string) {
  return d?.resumo.por_severidade[k] ?? 0;
}

const maxNasc = computed(() => Math.max(1, ...(evolucao.value?.meses.map((m) => m.nascimentos) ?? [1])));
function barH(n: number) { return n <= 0 ? 0 : Math.max(6, (n / maxNasc.value) * 100); }

const atalhos = [
  { to: "/registrar", emoji: "⚖️", label: "Registrar" },
  { to: "/rebanho", emoji: "🐂", label: "Rebanho" },
  { to: "/reproducao", emoji: "🧬", label: "Reprodução" },
  { to: "/nutricao", emoji: "🥗", label: "Nutrição" },
  { to: "/estoque", emoji: "🌽", label: "Estoque" },
  { to: "/financeiro", emoji: "💵", label: "Financeiro" },
  { to: "/mercado", emoji: "💰", label: "Mercado" },
  { to: "/alertas", emoji: "🔔", label: "Alertas" },
];

async function carregar() {
  carregando.value = true;
  erro.value = "";
  try {
    const [d, ev] = await Promise.all([getDashboard(), getEvolucaoRebanho()]);
    data.value = d;
    evolucao.value = ev;
    // ordena fazendas: mais crítica primeiro
    data.value.fazendas.sort((a, b) => b.alertas_abertos - a.alertas_abertos);
  } catch (e) {
    erro.value = String(e instanceof Error ? e.message : e);
    if (String(e).includes("expirada")) router.push("/login");
  } finally {
    carregando.value = false;
  }
}

onMounted(carregar);
</script>

<template>
  <AppShell title="Painel executivo" :sub="data?.organizacao" @refresh="carregar">
    <div class="page-heading">
      <div class="eyebrow">Visão consolidada</div>
      <h1>Situação do grupo</h1>
      <p>Indicadores e gatilhos das fazendas em tempo real. Ordenadas pela criticidade.</p>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="atalhos">
      <RouterLink v-for="a in atalhos" :key="a.to" :to="a.to" class="atalho">
        <span class="ax-emoji">{{ a.emoji }}</span>
        <span class="ax-label">{{ a.label }}</span>
      </RouterLink>
    </div>

    <div class="metrics" v-if="data">
      <KpiCard label="Fazendas" :value="data.resumo.fazendas" sub="no grupo" :icon="Warehouse" tone="blue" />
      <KpiCard label="Alertas abertos" :value="data.resumo.alertas_abertos" sub="exigem atenção"
               :icon="TriangleAlert" :tone="data.resumo.alertas_abertos ? 'danger' : 'primary'" />
      <KpiCard label="Ações críticas" :value="sev(data, 'ALERTA') + sev(data, 'CRITICO')"
               sub="ALERTA / CRÍTICO" :icon="TriangleAlert" tone="danger" />
      <KpiCard label="A avaliar / revisar" :value="sev(data, 'AVALIAR') + sev(data, 'REVISAR')"
               sub="decisões pendentes" :icon="Search" tone="amber" />
    </div>

    <Panel title="Evolução do rebanho" sub="nascimentos por mês — últimos 12 meses" v-if="evolucao" style="margin-bottom:22px">
      <template #actions>
        <div class="evo-legend">
          <span><b>{{ evolucao.total_ativos }}</b> ativos</span>
          <span class="sep">·</span>
          <span><b>{{ evolucao.total_nascimentos_12m }}</b> nascimentos/12m</span>
        </div>
      </template>
      <div class="evo" v-if="evolucao.total_nascimentos_12m > 0">
        <div class="evo-bar" v-for="m in evolucao.meses" :key="m.periodo" :title="`${m.label}/${m.ano}: ${m.nascimentos}`">
          <div class="evo-n">{{ m.nascimentos || "" }}</div>
          <div class="evo-track"><div class="evo-fill" :style="{ height: `${barH(m.nascimentos)}%` }" /></div>
          <div class="evo-lbl">{{ m.label }}</div>
        </div>
      </div>
      <p v-else class="evo-vazio">Sem nascimentos registrados nos últimos 12 meses. Conforme as datas de nascimento forem cadastradas, a curva aparece aqui.</p>
    </Panel>

    <div class="grid-panels" v-if="data">
      <Panel v-for="f in data.fazendas" :key="f.id" :title="f.nome"
             :sub="f.municipio ? `${f.municipio}/${f.uf}` : (f.uf ?? '')">
        <template #actions>
          <RouterLink :to="`/fazendas/${f.id}`" class="btn btn--secondary" style="height:34px">Detalhes</RouterLink>
        </template>
        <div style="display:flex;gap:8px;margin:4px 0 10px">
          <span v-if="f.alertas_abertos === 0" class="badge OK"><CircleCheck :size="13" /> tudo OK</span>
          <span v-else class="badge ALERTA"><TriangleAlert :size="13" /> {{ f.alertas_abertos }} alerta(s)</span>
        </div>
        <div class="kpirow" v-for="i in f.indicadores" :key="i.codigo">
          <div>
            <div class="kpirow__name">{{ i.nome }}</div>
            <div class="kpirow__val">
              {{ fmtValor(i.valor, i.formato, i.casas_decimais) }}
              <span v-if="i.referencia !== null" class="muted">
                · meta {{ fmtValor(i.referencia, i.formato, i.casas_decimais) }}
              </span>
            </div>
          </div>
          <StatusBadge :situacao="i.situacao" />
        </div>
      </Panel>
    </div>
  </AppShell>
</template>

<style scoped>
.atalhos { display: grid; grid-template-columns: repeat(8, 1fr); gap: 12px; margin-bottom: 22px; }
@media (max-width: 1000px) { .atalhos { grid-template-columns: repeat(4, 1fr); } }
@media (max-width: 560px) { .atalhos { grid-template-columns: repeat(3, 1fr); } }
.atalho {
  display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 14px 8px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  box-shadow: var(--shadow); text-align: center;
}
.atalho:hover { border-color: var(--primary); background: #f7fcfa; }
.ax-emoji { font-size: 24px; line-height: 1; }
.ax-label { font-size: 12.5px; font-weight: 600; color: var(--text); }

.evo-legend { display: flex; gap: 8px; align-items: center; font-size: 13px; color: var(--muted); }
.evo-legend b { color: var(--text); }
.evo-legend .sep { opacity: .5; }
.evo { display: flex; align-items: flex-end; gap: 10px; height: 160px; padding-top: 6px; }
.evo-bar { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; }
.evo-n { font-size: 11.5px; font-weight: 700; color: var(--text); height: 16px; font-variant-numeric: tabular-nums; }
.evo-track { flex: 1; width: 60%; max-width: 34px; display: flex; align-items: flex-end;
  background: #eef2f4; border-radius: 6px 6px 0 0; overflow: hidden; }
.evo-fill { width: 100%; background: var(--primary); border-radius: 6px 6px 0 0; transition: height .3s; }
.evo-lbl { font-size: 11.5px; color: var(--muted); margin-top: 6px; text-transform: capitalize; }
.evo-vazio { color: var(--muted); font-size: 13.5px; padding: 8px 2px; }
</style>
