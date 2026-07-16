<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { getAlertas, getFazendas, type Alerta, type Fazenda } from "../api";

const alertas = ref<Alerta[]>([]);
const fazendas = ref<Fazenda[]>([]);
const erro = ref("");
const busca = ref("");

const ordemSev: Record<string, number> = { CRITICO: 0, ALERTA: 1, AVALIAR: 2, REVISAR: 3, OK: 4 };

const nomeFazenda = (id: string) => fazendas.value.find((f) => f.id === id)?.nome ?? "—";

const filtrados = computed(() =>
  [...alertas.value]
    .sort((a, b) => (ordemSev[a.severidade] ?? 9) - (ordemSev[b.severidade] ?? 9))
    .filter((a) => {
      const q = busca.value.toLowerCase();
      return !q || a.mensagem.toLowerCase().includes(q) || nomeFazenda(a.fazenda_id).toLowerCase().includes(q);
    })
);

async function carregar() {
  erro.value = "";
  try {
    [alertas.value, fazendas.value] = await Promise.all([getAlertas(true), getFazendas()]);
  } catch (e) {
    erro.value = String(e instanceof Error ? e.message : e);
  }
}

onMounted(carregar);
</script>

<template>
  <AppShell title="Alertas" sub="Gatilhos disparados" @refresh="carregar">
    <div class="page-heading">
      <div class="eyebrow">Central de alertas</div>
      <h1>Alertas abertos</h1>
      <p>Todos os gatilhos disparados nas fazendas do grupo. Mais severos primeiro.</p>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <Panel>
      <template #actions>
        <div class="row" style="width:280px">
          <input class="input" v-model="busca" placeholder="Buscar por fazenda ou mensagem…" />
        </div>
      </template>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Situação</th>
              <th>Fazenda</th>
              <th>Ocorrência</th>
              <th>Valor</th>
              <th>Meta</th>
              <th>Ação recomendada</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in filtrados" :key="a.id">
              <td><StatusBadge :situacao="a.severidade" /></td>
              <td>{{ nomeFazenda(a.fazenda_id) }}</td>
              <td>{{ a.mensagem }}</td>
              <td>{{ a.valor_observado ?? "—" }}</td>
              <td class="muted">{{ a.valor_referencia ?? "—" }}</td>
              <td class="muted" :title="a.acao ?? ''">{{ a.acao ?? "—" }}</td>
            </tr>
            <tr v-if="filtrados.length === 0">
              <td colspan="6" class="muted" style="text-align:center;padding:24px">
                Nenhum alerta aberto. 🎉
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Panel>
  </AppShell>
</template>
