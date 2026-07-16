<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Zap, Check } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import {
  getFazendas, getParametros, updateParametro, getRegras,
  type Fazenda, type Parametro, type Regra,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const parametros = ref<Parametro[]>([]);
const regras = ref<Regra[]>([]);
const erro = ref("");
const salvo = ref<string>("");

// mapa chave-do-parametro -> regra que a usa (pra mostrar "gera alerta")
const regraPorChave = computed(() => {
  const m: Record<string, Regra> = {};
  for (const r of regras.value) if (r.parametro_chave) m[r.parametro_chave] = r;
  return m;
});

// parametros agrupados por grupo
const grupos = computed(() => {
  const g: Record<string, Parametro[]> = {};
  for (const p of parametros.value) (g[p.grupo ?? "Outros"] ??= []).push(p);
  return g;
});

const OPS: Record<string, string> = {
  ">": "passar de", ">=": "atingir ou passar de", "<": "cair abaixo de",
  "<=": "ficar em ou abaixo de", "==": "for igual a", "!=": "for diferente de",
  "abs_diff>": "desviar da",
};

function condicao(r: Regra): string {
  return `${r.indicador_nome} ${OPS[r.operador] ?? r.operador} ${valorRef(r)}`;
}
function valorRef(r: Regra): string {
  if (r.tipo_referencia === "parametro") return "esta meta";
  return String(r.valor_referencia ?? "");
}

async function carregar() {
  if (!fazendaId.value) return;
  erro.value = "";
  try {
    [parametros.value, regras.value] = await Promise.all([
      getParametros(fazendaId.value), getRegras(),
    ]);
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function init() {
  fazendas.value = await getFazendas();
  const sede = fazendas.value.find((f) => f.nome.includes("Sede")) ?? fazendas.value[0];
  if (sede) { fazendaId.value = sede.id; await carregar(); }
}
watch(fazendaId, carregar);

async function salvar(p: Parametro, valor: string) {
  const v = parseFloat(valor);
  if (isNaN(v) || v === p.valor) return;
  try {
    await updateParametro(fazendaId.value, p.chave, v);
    p.valor = v;
    salvo.value = p.chave;
    setTimeout(() => { if (salvo.value === p.chave) salvo.value = ""; }, 1800);
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}

onMounted(init);
</script>

<template>
  <AppShell title="Metas" sub="Limites que disparam os alertas" @refresh="carregar">
    <div class="head">
      <div class="eyebrow">Configuração</div>
      <h1>Metas da fazenda</h1>
      <p>Estas são as metas de cada fazenda. <b>O sistema dispara um alerta quando o indicador ultrapassa a meta.</b> Ex: se o custo da dieta passar de R$ 13,50/cab/dia, vira alerta. Edite um valor e ele passa a valer na hora.</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input selc" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <Panel v-for="(itens, grupo) in grupos" :key="grupo" :title="grupo" style="margin-bottom:16px">
      <div class="tbl-wrap">
        <table class="mtbl">
          <colgroup><col style="width:34%" /><col style="width:20%" /><col style="width:46%" /></colgroup>
          <thead><tr><th>Meta</th><th>Valor</th><th>O que dispara</th></tr></thead>
          <tbody>
            <tr v-for="p in itens" :key="p.chave">
              <td>
                <div class="rot">{{ p.rotulo }}</div>
                <div class="uni">{{ p.unidade }}</div>
              </td>
              <td>
                <div class="row" style="gap:8px">
                  <input class="input val tnum" :value="p.valor"
                         @change="salvar(p, ($event.target as HTMLInputElement).value)" />
                  <Check v-if="salvo === p.chave" :size="16" class="ok" />
                </div>
              </td>
              <td>
                <template v-if="regraPorChave[p.chave]">
                  <span :class="['badge', regraPorChave[p.chave].severidade]">
                    <Zap :size="12" /> {{ regraPorChave[p.chave].severidade }}
                  </span>
                  <span class="cond">se {{ condicao(regraPorChave[p.chave]) }}</span>
                </template>
                <span v-else class="muted" style="font-size:12.5px">não usada em alerta</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Panel>
  </AppShell>
</template>

<style scoped>
.selc { width: auto; min-width: 240px; appearance: auto; }
.tbl-wrap { overflow-x: auto; }
.mtbl { width: 100%; min-width: 480px; border-collapse: collapse; table-layout: fixed; }
.mtbl th, .mtbl td { padding: 12px 14px; text-align: left; vertical-align: middle; border-bottom: 1px solid var(--border); }
.mtbl tbody tr:last-child td { border-bottom: none; }
.mtbl th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600; }
.rot { font-size: 14px; font-weight: 600; }
.uni { font-size: 12px; color: var(--muted); }
.val { width: 110px; height: 36px; }
.ok { color: var(--primary); }
.cond { font-size: 12.5px; color: var(--muted); margin-left: 8px; }
</style>
