<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { RefreshCw, Search, ChevronLeft } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import {
  getFazendas, getAnimais, getRelatorioPesagem, pesarCampo, sincronizarFila, tamanhoFila,
  type Fazenda, type Animal,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const animais = ref<Animal[]>([]);
const ultimoPeso = ref<Record<string, number>>({});

const online = ref(navigator.onLine);
const fila = ref(tamanhoFila());

const busca = ref("");
const sel = ref<Animal | null>(null);
const peso = ref("");
const msg = ref("");
const erro = ref("");
const salvando = ref(false);
const sincronizando = ref(false);

function atualizarStatus() { online.value = navigator.onLine; }
async function aoVoltarOnline() { atualizarStatus(); await sincronizar(); }
// reflete o tamanho da fila mesmo quando a sincronização global (App.vue) esvazia
let timer: number | undefined;
onMounted(() => {
  window.addEventListener("online", aoVoltarOnline);
  window.addEventListener("offline", atualizarStatus);
  timer = window.setInterval(() => { online.value = navigator.onLine; fila.value = tamanhoFila(); }, 2000);
  init();
});
onUnmounted(() => {
  window.removeEventListener("online", aoVoltarOnline);
  window.removeEventListener("offline", atualizarStatus);
  if (timer) clearInterval(timer);
});

async function init() {
  fazendas.value = await getFazendas();
  if (fazendas.value[0]) { fazendaId.value = fazendas.value[0].id; await carregar(); }
}
async function carregar() {
  if (!fazendaId.value) return;
  animais.value = await getAnimais(fazendaId.value);
  try {
    const r = await getRelatorioPesagem(fazendaId.value);
    ultimoPeso.value = Object.fromEntries(r.animais.map((a) => [a.brinco, a.peso]));
  } catch { /* offline: segue sem o último peso */ }
}
watch(fazendaId, () => { sel.value = null; busca.value = ""; carregar(); });

const resultados = computed(() => {
  const q = busca.value.trim().toLowerCase();
  if (!q) return [];
  return animais.value
    .filter((a) => a.status === "ativo" && a.brinco.toLowerCase().includes(q))
    .slice(0, 8);
});

function escolher(a: Animal) { sel.value = a; busca.value = ""; peso.value = ""; msg.value = ""; erro.value = ""; }
function trocar() { sel.value = null; peso.value = ""; }

async function salvar() {
  const p = parseFloat(peso.value.replace(",", "."));
  if (!sel.value) { erro.value = "Escolha o animal."; return; }
  if (isNaN(p) || p <= 0 || p > 2000) { erro.value = "Informe um peso válido (kg)."; return; }
  salvando.value = true; erro.value = "";
  try {
    const brinco = sel.value.brinco;
    const r = await pesarCampo(sel.value.id, brinco, p);
    fila.value = tamanhoFila();
    ultimoPeso.value[brinco] = p;
    msg.value = r === "online" ? `✅ ${brinco}: ${p} kg registrado` : `📥 ${brinco}: ${p} kg salvo — vai sincronizar`;
    sel.value = null; peso.value = ""; // pronto pro próximo animal
  } catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}

async function sincronizar() {
  if (sincronizando.value) return;
  sincronizando.value = true;
  try {
    const r = await sincronizarFila();
    fila.value = r.pendente;
    if (r.ok) msg.value = `☁️ ${r.ok} pesagem(ns) enviada(s)`;
  } finally { sincronizando.value = false; }
}
</script>

<template>
  <AppShell title="Modo campo" sub="Pesar no curral" @refresh="carregar">
    <div class="campo">
      <!-- status -->
      <div class="status">
        <span class="pill" :class="online ? 'on' : 'off'">
          <span class="d" /> {{ online ? "Online" : "Offline" }}
        </span>
        <span v-if="fila" class="fila">📥 {{ fila }} na fila</span>
        <span class="grow" />
        <button v-if="fila" class="btn btn--secondary sinc" :disabled="!online || sincronizando" @click="sincronizar">
          <RefreshCw :size="15" /> Sincronizar
        </button>
      </div>

      <div class="row" style="gap:8px;margin:4px 0 14px">
        <span class="muted" style="font-size:13px">Fazenda:</span>
        <select class="input selc" v-model="fazendaId">
          <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
        </select>
      </div>

      <p v-if="msg" class="msg">{{ msg }}</p>

      <!-- 1) escolher animal -->
      <div v-if="!sel" class="bloco">
        <label class="lbl">1 · Animal (brinco)</label>
        <div class="search"><Search :size="18" class="muted" /><input class="binp" v-model="busca" placeholder="Digite o brinco…" inputmode="text" autofocus /></div>
        <div v-if="resultados.length" class="lista">
          <button v-for="a in resultados" :key="a.id" class="item" @click="escolher(a)">
            <div><div class="br">{{ a.brinco }}</div><div class="cat">{{ a.categoria ?? "—" }} · {{ a.raca ?? "—" }}</div></div>
            <div v-if="ultimoPeso[a.brinco]" class="ult">última<br><b>{{ ultimoPeso[a.brinco] }} kg</b></div>
          </button>
        </div>
        <p v-else-if="busca" class="vazio">Nenhum animal com esse brinco.</p>
      </div>

      <!-- 2) pesar -->
      <div v-else class="bloco">
        <div class="selrow">
          <button class="volta" @click="trocar"><ChevronLeft :size="18" /></button>
          <div><div class="br big">{{ sel.brinco }}</div><div class="cat">{{ sel.categoria ?? "—" }} · {{ sel.raca ?? "—" }}<span v-if="ultimoPeso[sel.brinco]"> · última {{ ultimoPeso[sel.brinco] }} kg</span></div></div>
        </div>
        <label class="lbl" style="margin-top:16px">2 · Peso hoje (kg)</label>
        <input class="peso" v-model="peso" inputmode="decimal" placeholder="0" @keyup.enter="salvar" />
        <p v-if="erro" class="error">{{ erro }}</p>
        <button class="btn btn--primary salvar" :disabled="salvando" @click="salvar">Salvar pesagem</button>
      </div>

      <p class="dica">💡 Sem sinal? Pode registrar do mesmo jeito — o app guarda e envia sozinho quando a internet voltar.</p>
    </div>
  </AppShell>
</template>

<style scoped>
.campo { max-width: 520px; margin: 0 auto; }
.status { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.pill { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; font-weight: 700; padding: 4px 11px; border-radius: 999px; }
.pill .d { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.pill.on { background: #e7f5ef; color: #0a6b4c; } .pill.off { background: #fdf1e3; color: #9a5a09; }
.fila { font-size: 12.5px; color: var(--muted); font-weight: 600; }
.grow { flex: 1; }
.sinc { height: 32px; }
.selc { width: auto; min-width: 200px; appearance: auto; }
.msg { background: #e7f5ef; color: #0a6b4c; border: 1px solid #bfe0d0; border-radius: 10px; padding: 10px 13px; font-weight: 600; font-size: 14px; }
.bloco { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 16px; box-shadow: var(--shadow); }
.lbl { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); display: block; margin-bottom: 8px; }
.search { display: flex; align-items: center; gap: 8px; border: 1px solid var(--border); border-radius: 11px; padding: 12px 14px; }
.binp { border: none; outline: none; font-size: 18px; flex: 1; background: transparent; color: var(--text); }
.lista { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.item { display: flex; align-items: center; justify-content: space-between; gap: 10px; text-align: left;
  background: var(--surface); border: 1px solid var(--border); border-radius: 11px; padding: 13px 14px; cursor: pointer; }
.item:hover { border-color: var(--primary); background: #f7fcfa; }
.item .br { font-size: 17px; font-weight: 700; } .item .br.big { font-size: 24px; }
.item .cat { font-size: 12.5px; color: var(--muted); }
.ult { font-size: 11px; color: var(--muted); text-align: right; } .ult b { color: var(--text); font-size: 14px; }
.selrow { display: flex; align-items: center; gap: 12px; }
.br { font-size: 17px; font-weight: 700; } .br.big { font-size: 26px; }
.cat { font-size: 12.5px; color: var(--muted); }
.volta { width: 38px; height: 38px; border-radius: 10px; border: 1px solid var(--border); background: var(--surface); display: grid; place-items: center; cursor: pointer; flex: none; }
.peso { width: 100%; text-align: center; font-size: 56px; font-weight: 800; border: 2px solid var(--border); border-radius: 16px; padding: 14px; outline: none; color: var(--text); }
.peso:focus { border-color: var(--primary); }
.salvar { width: 100%; height: 56px; font-size: 18px; margin-top: 14px; border-radius: 14px; }
.vazio { color: var(--muted); font-size: 14px; padding: 12px 2px; }
.dica { font-size: 13px; color: var(--muted); margin-top: 16px; line-height: 1.5; }
</style>
