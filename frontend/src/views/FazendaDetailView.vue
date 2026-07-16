<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ArrowLeft, Check } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import StatusBadge from "../components/StatusBadge.vue";
import {
  getPainelFazenda, getParametros, lancarValor, updateParametro,
  fmtValor, type FazendaPainel, type Parametro,
} from "../api";

const route = useRoute();
const id = route.params.id as string;

const painel = ref<FazendaPainel | null>(null);
const parametros = ref<Parametro[]>([]);
const erro = ref("");
const salvando = ref("");

// edicao inline de valor lancado
const novoValor = ref<Record<string, string>>({});

async function carregar() {
  erro.value = "";
  try {
    [painel.value, parametros.value] = await Promise.all([
      getPainelFazenda(id), getParametros(id),
    ]);
  } catch (e) {
    erro.value = String(e instanceof Error ? e.message : e);
  }
}

async function salvarValor(codigo: string) {
  const v = parseFloat(novoValor.value[codigo]);
  if (isNaN(v)) return;
  salvando.value = codigo;
  try {
    await lancarValor(id, codigo, v);
    novoValor.value[codigo] = "";
    await carregar();
  } finally {
    salvando.value = "";
  }
}

async function salvarMeta(p: Parametro, valor: string) {
  const v = parseFloat(valor);
  if (isNaN(v) || v === p.valor) return;
  salvando.value = p.chave;
  try {
    await updateParametro(id, p.chave, v);
    await carregar();
  } finally {
    salvando.value = "";
  }
}

onMounted(carregar);
</script>

<template>
  <AppShell :title="painel?.nome ?? 'Fazenda'"
            :sub="painel?.municipio ? `${painel.municipio}/${painel.uf}` : ''" @refresh="carregar">
    <div class="page-heading">
      <RouterLink to="/fazendas" class="row muted" style="font-size:13px;margin-bottom:6px">
        <ArrowLeft :size="15" /> Fazendas
      </RouterLink>
      <div class="eyebrow">Detalhe da unidade</div>
      <h1>{{ painel?.nome }}</h1>
      <p>Indicadores, ações recomendadas e metas. Lançar um valor reavalia os gatilhos na hora.</p>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div style="display:grid;grid-template-columns:1.6fr 1fr;gap:16px" v-if="painel">
      <Panel title="Indicadores e gatilhos" sub="Situação atual de cada KPI">
        <div style="overflow-x:auto">
          <table class="data-table">
            <thead>
              <tr><th>Indicador</th><th>Valor</th><th>Meta</th><th>Situação</th><th>Lançar</th></tr>
            </thead>
            <tbody>
              <tr v-for="i in painel.indicadores" :key="i.codigo">
                <td>
                  <strong>{{ i.nome }}</strong>
                  <div class="muted" v-if="i.situacao !== 'OK' && i.acao" style="font-size:12px;max-width:280px">{{ i.acao }}</div>
                </td>
                <td>{{ fmtValor(i.valor, i.formato, i.casas_decimais) }}</td>
                <td class="muted">{{ fmtValor(i.referencia, i.formato, i.casas_decimais) }}</td>
                <td><StatusBadge :situacao="i.situacao" /></td>
                <td>
                  <div class="row" style="gap:6px">
                    <input class="input" style="height:34px;width:90px" v-model="novoValor[i.codigo]"
                           placeholder="valor" @keyup.enter="salvarValor(i.codigo)" />
                    <button class="btn btn--primary btn--icon" style="height:34px;width:34px"
                            :disabled="salvando === i.codigo" @click="salvarValor(i.codigo)">
                      <Check :size="15" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Metas / premissas" sub="Editar recalcula os gatilhos">
        <div style="overflow-x:auto">
          <table class="data-table">
            <thead><tr><th>Meta</th><th>Valor</th><th></th></tr></thead>
            <tbody>
              <tr v-for="p in parametros" :key="p.chave">
                <td>
                  <div>{{ p.rotulo }}</div>
                  <div class="muted" style="font-size:11.5px">{{ p.grupo }} · {{ p.unidade }}</div>
                </td>
                <td>
                  <input class="input" style="height:32px;width:90px" :value="p.valor"
                         @change="salvarMeta(p, ($event.target as HTMLInputElement).value)" />
                </td>
                <td class="muted" style="font-size:11px">{{ salvando === p.chave ? "…" : "" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  </AppShell>
</template>
