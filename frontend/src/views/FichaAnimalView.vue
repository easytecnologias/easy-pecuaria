<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, Scale, Pencil, Trash2 } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import Modal from "../components/Modal.vue";
import {
  getFicha, lancarPesagem, atualizarAnimal, excluirAnimal, getLotes,
  type FichaAnimal, type Lote,
} from "../api";

const route = useRoute();
const router = useRouter();
const id = route.params.id as string;
const ficha = ref<FichaAnimal | null>(null);
const erro = ref("");
const peso = ref<string>("");
const salvando = ref(false);
const META_GMD = 1.55;

const fmtData = (d: string) => d.split("-").reverse().join("/");

// pesagens em ordem crescente (para timeline e grafico)
const pesagensAsc = computed(() =>
  ficha.value ? [...ficha.value.pesagens].sort((a, b) => a.data.localeCompare(b.data)) : []
);

// linha do tempo: nascimento + pesagens + inseminações + diagnósticos (ordenado por data)
const eventos = computed(() => {
  const a = ficha.value?.animal;
  const evs: { data: string; titulo: string; sub: string; warn?: boolean }[] = [];
  if (a?.data_nascimento)
    evs.push({ data: a.data_nascimento, titulo: "Nascimento", sub: `${fmtData(a.data_nascimento)}${a.mae_brinco ? ` · mãe ${a.mae_brinco}` : ""}` });
  for (const p of ficha.value?.pesagens ?? [])
    evs.push({
      data: p.data, titulo: `Pesagem · ${p.peso} kg`,
      sub: `${fmtData(p.data)}${p.gmd !== null ? ` · GMD ${p.gmd} kg/dia no período` : " · pesagem base"}`,
    });
  for (const i of ficha.value?.inseminacoes ?? []) {
    evs.push({ data: i.data, titulo: `IATF · ${i.touro}`, sub: `${fmtData(i.data)}${i.inseminador ? ` · ${i.inseminador}` : ""}` });
    if (i.resultado !== "pendente" && i.dg_data)
      evs.push({
        data: i.dg_data, warn: i.resultado === "vazia",
        titulo: `Diagnóstico: ${i.resultado === "prenhe" ? "PRENHE" : "VAZIA"}`,
        sub: fmtData(i.dg_data),
      });
  }
  const rotSan: Record<string, string> = { vacina: "Vacina", vermifugo: "Vermífugo", tratamento: "Tratamento", exame: "Exame", carrapaticida: "Carrapaticida", hormonio: "Hormônio" };
  for (const s of ficha.value?.sanitarios ?? [])
    evs.push({
      data: s.data, titulo: `${rotSan[s.tipo] ?? s.tipo} · ${s.produto}`,
      sub: `${fmtData(s.data)}${s.dose ? ` · ${s.dose}` : ""}${s.proxima_aplicacao ? ` · próxima ${fmtData(s.proxima_aplicacao)}` : ""}`,
    });
  const rotMov: Record<string, string> = { compra: "Compra", venda: "Venda", morte: "Morte", descarte: "Descarte", transferencia: "Transferência de lote" };
  for (const m of ficha.value?.movimentos ?? [])
    evs.push({
      data: m.data, warn: m.tipo === "morte" || m.tipo === "descarte",
      titulo: `${rotMov[m.tipo] ?? m.tipo}${m.valor !== null ? ` · R$ ${m.valor.toFixed(2)}` : ""}`,
      sub: `${fmtData(m.data)}${m.motivo ? ` · ${m.motivo}` : ""}`,
    });
  return evs.sort((a, b) => a.data.localeCompare(b.data));
});

// sparkline de peso
const barras = computed(() => {
  const ps = pesagensAsc.value.map((p) => p.peso);
  if (!ps.length) return [];
  const min = Math.min(...ps), max = Math.max(...ps);
  const span = max - min || 1;
  return ps.map((v, i) => ({ h: 32 + 58 * ((v - min) / span), last: i === ps.length - 1 }));
});
const pesoInicial = computed(() => pesagensAsc.value[0]?.peso ?? null);
const pesoFinal = computed(() => pesagensAsc.value[pesagensAsc.value.length - 1]?.peso ?? null);

const gmdOk = computed(() => (ficha.value?.gmd_atual ?? 0) >= META_GMD);

async function carregar() {
  erro.value = "";
  try {
    ficha.value = await getFicha(id);
    lotes.value = await getLotes(ficha.value.animal.fazenda_id);
  }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
async function registrar() {
  const p = parseFloat(peso.value);
  if (isNaN(p)) return;
  salvando.value = true;
  try { ficha.value = await lancarPesagem(id, p); peso.value = ""; }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
  finally { salvando.value = false; }
}
onMounted(carregar);

// ---- editar / excluir animal ----
const CATS = ["Bezerro", "Bezerra", "Novilha", "Garrote", "Matriz", "Touro", "Boi"];
const modalEdit = ref(false);
const lotes = ref<Lote[]>([]);
const erroEdit = ref("");
const salvandoEdit = ref(false);
const form = ref({ brinco: "", categoria: "", raca: "", sexo: "M", data_nascimento: "",
  lote_id: "", mae_brinco: "", pai: "", status: "ativo" });

function abrirEdicao() {
  const a = ficha.value!.animal;
  form.value = {
    brinco: a.brinco, categoria: a.categoria ?? "", raca: a.raca ?? "", sexo: a.sexo ?? "M",
    data_nascimento: a.data_nascimento ?? "", lote_id: a.lote_id ?? "",
    mae_brinco: a.mae_brinco ?? "", pai: a.pai ?? "", status: a.status,
  };
  erroEdit.value = "";
  modalEdit.value = true;
}
async function salvarEdicao() {
  if (!form.value.brinco.trim()) { erroEdit.value = "O brinco é obrigatório."; return; }
  salvandoEdit.value = true; erroEdit.value = "";
  try {
    await atualizarAnimal(id, {
      brinco: form.value.brinco, categoria: form.value.categoria || undefined,
      raca: form.value.raca || undefined, sexo: form.value.sexo || undefined,
      data_nascimento: form.value.data_nascimento || null,
      lote_id: form.value.lote_id || null, mae_brinco: form.value.mae_brinco || undefined,
      pai: form.value.pai || undefined, status: form.value.status,
    });
    modalEdit.value = false;
    await carregar();
  } catch (e) { erroEdit.value = String(e instanceof Error ? e.message : e); }
  finally { salvandoEdit.value = false; }
}
async function removerAnimal() {
  if (!confirm(`Excluir o animal ${ficha.value?.animal.brinco}? Esta ação não pode ser desfeita.`)) return;
  try { await excluirAnimal(id); router.push("/rebanho"); }
  catch (e) { erro.value = String(e instanceof Error ? e.message : e); }
}
</script>

<template>
  <AppShell :title="ficha?.animal.brinco ?? 'Ficha'" sub="Ficha do animal" @refresh="carregar">
    <div class="head" style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px">
      <div>
        <RouterLink to="/rebanho" class="row muted" style="font-size:13px;margin-bottom:6px">
          <ArrowLeft :size="15" /> Rebanho
        </RouterLink>
        <div class="eyebrow">Histórico do animal</div>
        <h1>{{ ficha?.animal.brinco }}
          <span class="muted" style="font-size:18px" v-if="ficha">· {{ ficha.animal.categoria }} {{ ficha.animal.raca }}</span>
        </h1>
        <p>A ficha é a linha do tempo do bicho: nascimento, pesagens e (em breve) vacinas, cios e diagnósticos. Nada se apaga — é o histórico auditável que a rastreabilidade (SISBOV) exige.</p>
      </div>
      <div class="row" style="gap:8px;flex-shrink:0" v-if="ficha">
        <button class="btn btn--secondary" @click="abrirEdicao"><Pencil :size="15" /> Editar</button>
        <button class="btn btn--secondary danger" @click="removerAnimal"><Trash2 :size="15" /> Excluir</button>
      </div>
    </div>

    <p v-if="erro" class="error">{{ erro }}</p>

    <div class="ficha-grid" v-if="ficha">
      <!-- Linha do tempo -->
      <Panel title="Linha do tempo" sub="eventos registrados">
        <template #actions><span class="badge OK"><span class="dot" /> {{ ficha.animal.status }}</span></template>
        <div class="tl">
          <div class="ev" :class="{ warn: e.warn }" v-for="(e, i) in eventos" :key="i">
            <div class="ev-t">{{ e.titulo }}</div>
            <div class="ev-d">{{ e.sub }}</div>
          </div>
          <div v-if="!eventos.length" class="muted" style="padding:12px">Sem eventos ainda.</div>
        </div>
      </Panel>

      <div style="display:flex;flex-direction:column;gap:16px">
        <!-- Ganho de peso -->
        <Panel title="Ganho de peso" sub="últimas pesagens">
          <div class="spark" v-if="barras.length">
            <span v-for="(b, i) in barras" :key="i" :class="{ last: b.last }" :style="{ height: b.h + '%' }" />
          </div>
          <div v-else class="muted" style="padding:8px 0">Sem pesagens ainda.</div>
          <div class="row" style="justify-content:space-between;margin-top:8px">
            <span class="muted tnum">{{ pesoInicial ?? "—" }}kg</span>
            <span class="muted">→</span>
            <span class="muted tnum">{{ pesoFinal ?? "—" }}kg</span>
          </div>
          <div class="row" style="justify-content:space-between;margin-top:10px;align-items:center">
            <span class="muted" style="font-size:13px">GMD calculado</span>
            <span v-if="ficha.gmd_atual !== null" :class="['badge', gmdOk ? 'OK' : 'ALERTA']">
              <span class="dot" /> {{ ficha.gmd_atual }} kg/dia
            </span>
            <span v-else class="muted">—</span>
          </div>
        </Panel>

        <!-- Registrar pesagem -->
        <Panel title="Registrar pesagem" sub="o evento que alimenta o sistema">
          <div class="row" style="align-items:flex-end;gap:10px">
            <div class="field" style="flex:1"><label>Peso hoje (kg)</label>
              <input class="input tnum" v-model="peso" type="number" placeholder="ex: 490" @keyup.enter="registrar" />
            </div>
            <button class="btn p" :disabled="salvando" @click="registrar"><Scale :size="16" /> Registrar</button>
          </div>
          <div class="hint">💡 GMD = (peso novo − anterior) ÷ dias. Meta: {{ META_GMD }} kg/dia. Ao salvar, sobe pro painel e reavalia o gatilho.</div>
        </Panel>

        <!-- Ficha -->
        <Panel title="Ficha">
          <div class="attrs">
            <div><div class="k">Brinco</div>{{ ficha.animal.brinco }}</div>
            <div><div class="k">Categoria</div>{{ ficha.animal.categoria ?? "—" }}</div>
            <div><div class="k">Raça</div>{{ ficha.animal.raca ?? "—" }}</div>
            <div><div class="k">Nascimento</div>{{ ficha.animal.data_nascimento ? fmtData(ficha.animal.data_nascimento) : "—" }}</div>
            <div><div class="k">Mãe</div>{{ ficha.animal.mae_brinco ?? "—" }}</div>
            <div><div class="k">Pai</div>{{ ficha.animal.pai ?? "—" }}</div>
          </div>
        </Panel>
      </div>
    </div>

    <Modal v-if="modalEdit" titulo="Editar animal" sub="corrija os dados do animal" @fechar="modalEdit = false">
      <div class="eform">
        <div class="two">
          <div class="field"><label>Brinco *</label><input class="input" v-model="form.brinco" /></div>
          <div class="field"><label>Categoria</label>
            <select class="input selc" v-model="form.categoria">
              <option value="">—</option><option v-for="c in CATS" :key="c">{{ c }}</option>
            </select>
          </div>
        </div>
        <div class="two">
          <div class="field"><label>Raça</label><input class="input" v-model="form.raca" /></div>
          <div class="field"><label>Sexo</label>
            <select class="input selc" v-model="form.sexo"><option value="M">Macho</option><option value="F">Fêmea</option></select>
          </div>
        </div>
        <div class="two">
          <div class="field"><label>Nascimento</label><input class="input" type="date" v-model="form.data_nascimento" /></div>
          <div class="field"><label>Lote</label>
            <select class="input selc" v-model="form.lote_id">
              <option value="">— sem lote —</option>
              <option v-for="l in lotes" :key="l.id" :value="l.id">{{ l.nome }}</option>
            </select>
          </div>
        </div>
        <div class="two">
          <div class="field"><label>Mãe (brinco)</label><input class="input" v-model="form.mae_brinco" /></div>
          <div class="field"><label>Pai</label><input class="input" v-model="form.pai" /></div>
        </div>
        <div class="field"><label>Situação</label>
          <select class="input selc" v-model="form.status">
            <option value="ativo">Ativo</option><option value="vendido">Vendido</option><option value="morto">Morto</option>
          </select>
        </div>
        <p v-if="erroEdit" class="error">{{ erroEdit }}</p>
      </div>
      <template #acoes>
        <button class="btn btn--secondary" @click="modalEdit = false">Cancelar</button>
        <button class="btn btn--primary" :disabled="salvandoEdit" @click="salvarEdicao">Salvar</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.ficha-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; align-items: start; }
@media (max-width: 900px) { .ficha-grid { grid-template-columns: 1fr; } }

/* timeline */
.tl { position: relative; padding-left: 22px; }
.tl:before { content: ""; position: absolute; left: 5px; top: 6px; bottom: 6px; width: 2px; background: var(--border); }
.ev { position: relative; padding: 9px 0; }
.ev:before { content: ""; position: absolute; left: -22px; top: 13px; width: 11px; height: 11px; border-radius: 50%; background: #fff; border: 2px solid var(--primary); }
.ev.warn:before { border-color: var(--amber); }
.ev-t { font-size: 14px; font-weight: 600; }
.ev-d { font-size: 12.5px; color: var(--muted); margin-top: 1px; }

/* sparkline */
.spark { display: flex; align-items: flex-end; gap: 5px; height: 60px; }
.spark > span { flex: 1; background: #cfe6da; border-radius: 3px 3px 0 0; min-height: 6px; }
.spark > span.last { background: var(--primary); }

.attrs { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 16px; font-size: 14px; }
.attrs .k { font-size: 11.5px; color: var(--muted); text-transform: uppercase; letter-spacing: .03em; margin-bottom: 1px; }
.hint { background: #f2f8f5; border: 1px solid #cfe6da; border-radius: 8px; padding: 10px 12px; font-size: 12.5px; color: #245c47; margin-top: 12px; }

.btn.danger { color: var(--danger); }
.btn.danger:hover { background: #fcebeb; border-color: #f0c9c9; }
.eform { display: flex; flex-direction: column; gap: 12px; }
.eform .two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
@media (max-width: 620px) { .eform .two { grid-template-columns: 1fr; } }
.eform .field { display: grid; gap: 6px; align-content: start; }
.eform .field label { font-size: 12.5px; font-weight: 600; color: var(--text); }
.eform .field .input { width: 100%; }
.selc { appearance: auto; }
</style>
