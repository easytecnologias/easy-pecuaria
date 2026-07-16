<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { CircleCheck } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Modal from "../components/Modal.vue";
import {
  getFazendas, getLotes, getAnimais, criarAnimal, criarLote, lancarPesagem,
  type Fazenda, type Lote, type Animal,
} from "../api";

const fazendas = ref<Fazenda[]>([]);
const fazendaId = ref("");
const lotes = ref<Lote[]>([]);
const animais = ref<Animal[]>([]);
const modo = ref<"" | "animal" | "lote" | "pesagem">("");
const msg = ref("");
const erro = ref("");
const salvando = ref(false);

// tipos de registro
const tipos = [
  { id: "animal", emoji: "🐄", titulo: "Cadastrar animal", desc: "Um bicho novo no rebanho", ativo: true },
  { id: "lote", emoji: "📦", titulo: "Criar lote", desc: "Uma turma/grupo de manejo", ativo: true },
  { id: "pesagem", emoji: "⚖️", titulo: "Registrar pesagem", desc: "Peso de hoje → vira GMD", ativo: true },
  { id: "iatf", emoji: "🧬", titulo: "Inseminação (IATF)", desc: "Reprodução da cria", ativo: true },
  { id: "vacina", emoji: "💉", titulo: "Vacina / sanidade", desc: "Em breve", ativo: false },
  { id: "venda", emoji: "💰", titulo: "Venda / abate", desc: "Em breve", ativo: false },
];

// forms
const fAnimal = ref({ brinco: "", categoria: "Garrote", sexo: "M", raca: "", data_nascimento: "", lote_id: "", mae_brinco: "", pai: "" });
const fLote = ref({ nome: "", categoria: "Engorda", local: "" });
const fPes = ref({ animal_id: "", peso: "" });

const META = {
  animal: { titulo: "Cadastrar animal", sub: "preencha o que souber — o resto pode ficar em branco", label: "Cadastrar animal", largura: 560 },
  lote: { titulo: "Criar lote", sub: "uma turma de animais manejada junta", label: "Criar lote", largura: 460 },
  pesagem: { titulo: "Registrar pesagem", sub: "o peso de hoje vira GMD automaticamente", label: "Registrar pesagem", largura: 460 },
} as const;
const meta = computed(() => (modo.value ? META[modo.value] : null));

function fechar() { modo.value = ""; msg.value = ""; erro.value = ""; }

async function carregarListas() {
  if (!fazendaId.value) return;
  [lotes.value, animais.value] = await Promise.all([getLotes(fazendaId.value), getAnimais(fazendaId.value)]);
}

async function init() {
  fazendas.value = await getFazendas();
  const sede = fazendas.value.find((f) => f.nome.includes("Sede")) ?? fazendas.value[0];
  if (sede) { fazendaId.value = sede.id; await carregarListas(); }
}
watch(fazendaId, carregarListas);

const router = useRouter();
function escolher(id: string, ativo: boolean) {
  if (!ativo) return;
  if (id === "iatf") { router.push("/reproducao"); return; }
  modo.value = id as any;
  msg.value = ""; erro.value = "";
}

async function salvar() {
  salvando.value = true; msg.value = ""; erro.value = "";
  try {
    if (modo.value === "animal") {
      if (!fAnimal.value.brinco) throw new Error("Informe o brinco (identificação do animal).");
      const a = await criarAnimal(fazendaId.value, {
        brinco: fAnimal.value.brinco, categoria: fAnimal.value.categoria, sexo: fAnimal.value.sexo,
        raca: fAnimal.value.raca || undefined, data_nascimento: fAnimal.value.data_nascimento || null,
        lote_id: fAnimal.value.lote_id || null, mae_brinco: fAnimal.value.mae_brinco || undefined,
        pai: fAnimal.value.pai || undefined, origem: "nascido",
      });
      msg.value = `Animal ${a.brinco} cadastrado com sucesso.`;
      fAnimal.value.brinco = ""; fAnimal.value.mae_brinco = "";
    } else if (modo.value === "lote") {
      if (!fLote.value.nome) throw new Error("Dê um nome ao lote.");
      const l = await criarLote(fazendaId.value, { nome: fLote.value.nome, categoria: fLote.value.categoria, local: fLote.value.local || undefined });
      msg.value = `Lote "${l.nome}" criado com sucesso.`;
      fLote.value.nome = ""; fLote.value.local = "";
    } else if (modo.value === "pesagem") {
      if (!fPes.value.animal_id) throw new Error("Escolha o animal.");
      const p = parseFloat(fPes.value.peso);
      if (isNaN(p)) throw new Error("Informe o peso em kg.");
      const ficha = await lancarPesagem(fPes.value.animal_id, p);
      const g = ficha.gmd_atual;
      msg.value = g !== null
        ? `Pesagem registrada. GMD calculado: ${g} kg/dia.`
        : "Pesagem registrada (é a primeira, serve de base).";
      fPes.value.peso = "";
    }
    await carregarListas();
  } catch (e) {
    erro.value = String(e instanceof Error ? e.message : e);
  } finally {
    salvando.value = false;
  }
}
onMounted(init);
</script>

<template>
  <AppShell title="Registrar" sub="Inserir dados no sistema" @refresh="carregarListas">
    <div class="head">
      <div class="eyebrow">Inserir dados</div>
      <h1>O que você quer anotar?</h1>
      <p>Você anota fatos simples (nasceu, pesou, vacinou). O sistema calcula os indicadores sozinho. Escolha abaixo:</p>
    </div>

    <div class="row" style="margin-bottom:16px;gap:8px">
      <span class="muted" style="font-size:13px">Fazenda:</span>
      <select class="input" style="width:auto;min-width:220px;appearance:auto" v-model="fazendaId">
        <option v-for="f in fazendas" :key="f.id" :value="f.id">{{ f.nome }}</option>
      </select>
    </div>

    <!-- cartoes de tipo -->
    <div class="tipos">
      <button v-for="t in tipos" :key="t.id" class="tipo" :class="{ on: modo === t.id, off: !t.ativo }"
              @click="escolher(t.id, t.ativo)">
        <span class="emo">{{ t.emoji }}</span>
        <span>
          <span class="tt">{{ t.titulo }}</span>
          <span class="td">{{ t.desc }}</span>
        </span>
      </button>
    </div>

    <p v-if="msg && !modo" class="ok-msg"><CircleCheck :size="16" /> {{ msg }}</p>
    <p class="muted" style="margin-top:8px">👆 Escolha um tipo acima para abrir o formulário.</p>

    <Modal v-if="modo && meta" :titulo="meta.titulo" :sub="meta.sub" :largura="meta.largura" @fechar="fechar">
      <div class="form">
        <!-- CADASTRAR ANIMAL -->
        <template v-if="modo === 'animal'">
          <div class="field"><label>Brinco *</label>
            <input class="input" v-model="fAnimal.brinco" placeholder="ex: JLN-0421" />
            <span class="hint">O número do brinco na orelha. É a identificação do animal.</span>
          </div>
          <div class="two">
            <div class="field"><label>Categoria (fase de vida)</label>
              <select class="input sel" v-model="fAnimal.categoria">
                <option>Bezerro</option><option>Bezerra</option><option>Novilha</option>
                <option>Garrote</option><option>Matriz</option><option>Touro</option><option>Boi</option>
              </select>
              <span class="hint">Bezerro=filhote · Novilha=fêmea jovem · Garrote=macho em engorda · Matriz=vaca mãe.</span>
            </div>
            <div class="field"><label>Sexo</label>
              <select class="input sel" v-model="fAnimal.sexo"><option value="M">Macho</option><option value="F">Fêmea</option></select>
            </div>
          </div>
          <div class="two">
            <div class="field"><label>Raça</label>
              <input class="input" v-model="fAnimal.raca" placeholder="ex: Nelore, F1 Angus" />
              <span class="hint">A raça ou cruzamento do animal.</span>
            </div>
            <div class="field"><label>Nascimento</label>
              <input class="input" type="date" v-model="fAnimal.data_nascimento" />
              <span class="hint">Se souber a data. Pode deixar vazio.</span>
            </div>
          </div>
          <div class="field"><label>Lote (turma)</label>
            <select class="input sel" v-model="fAnimal.lote_id">
              <option value="">— sem lote —</option>
              <option v-for="l in lotes" :key="l.id" :value="l.id">{{ l.nome }}</option>
            </select>
            <span class="hint">Em qual grupo de manejo ele fica. Não tem lote ainda? Crie um primeiro.</span>
          </div>
          <div class="two">
            <div class="field"><label>Mãe (brinco)</label>
              <input class="input" v-model="fAnimal.mae_brinco" placeholder="ex: JLN-0088" />
              <span class="hint">Brinco da mãe, se souber (genealogia).</span>
            </div>
            <div class="field"><label>Pai (touro/sêmen)</label>
              <input class="input" v-model="fAnimal.pai" placeholder="ex: Angus FP" />
            </div>
          </div>
        </template>

        <!-- CRIAR LOTE -->
        <template v-else-if="modo === 'lote'">
          <div class="field"><label>Nome do lote *</label>
            <input class="input" v-model="fLote.nome" placeholder="ex: Garrotes Confinamento A" />
            <span class="hint">Um nome que identifique a turma.</span>
          </div>
          <div class="field"><label>Categoria</label>
            <select class="input sel" v-model="fLote.categoria">
              <option>Matrizes</option><option>Engorda</option><option>Bezerros</option>
              <option>Novilhas</option><option>Recria</option>
            </select>
            <span class="hint">O tipo do grupo. "Engorda" conta pra ocupação do confinamento.</span>
          </div>
          <div class="field"><label>Local</label>
            <input class="input" v-model="fLote.local" placeholder="ex: Pasto 3, Curral 1" />
            <span class="hint">Onde a turma fica.</span>
          </div>
        </template>

        <!-- REGISTRAR PESAGEM -->
        <template v-else-if="modo === 'pesagem'">
          <div class="field"><label>Animal *</label>
            <select class="input sel" v-model="fPes.animal_id">
              <option value="">— escolha o animal —</option>
              <option v-for="a in animais" :key="a.id" :value="a.id">{{ a.brinco }} · {{ a.categoria }} {{ a.raca }}</option>
            </select>
            <span class="hint">Qual animal você pesou na balança.</span>
          </div>
          <div class="field"><label>Peso hoje (kg) *</label>
            <input class="input tnum" type="number" v-model="fPes.peso" placeholder="ex: 490" />
            <span class="hint">O peso medido hoje. O sistema compara com a anterior e calcula o GMD.</span>
          </div>
        </template>

        <p v-if="msg" class="ok-msg"><CircleCheck :size="16" /> {{ msg }}</p>
        <p v-if="erro" class="error">{{ erro }}</p>
      </div>

      <template #acoes>
        <button class="btn btn--secondary" @click="fechar">Fechar</button>
        <button class="btn btn--primary" :disabled="salvando" @click="salvar">{{ meta.label }}</button>
      </template>
    </Modal>
  </AppShell>
</template>

<style scoped>
.tipos { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 18px; }
@media (max-width: 760px) { .tipos { grid-template-columns: 1fr 1fr; } }
.tipo { display: flex; align-items: center; gap: 12px; text-align: left; background: var(--surface);
  border: 1px solid var(--border); border-radius: 10px; padding: 14px; cursor: pointer; font: inherit; }
.tipo:hover { border-color: #b9cbd6; }
.tipo.on { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(7,139,100,.12); }
.tipo.off { opacity: .5; cursor: not-allowed; }
.tipo .emo { font-size: 26px; line-height: 1; }
.tipo .tt { display: block; font-weight: 700; font-size: 14.5px; }
.tipo .td { display: block; font-size: 12.5px; color: var(--muted); }

.form { display: flex; flex-direction: column; gap: 14px; padding: 4px 0; }
.form .two { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 16px; align-items: start; }
@media (max-width: 620px) { .form .two { grid-template-columns: 1fr; } }
.form .field { display: grid; gap: 6px; align-content: start; }
.form .field label { font-size: 13px; color: var(--text); font-weight: 600; }
.form .field .input { width: 100%; }
.hint { font-size: 12px; color: var(--muted); line-height: 1.35; }
.sel { appearance: auto; }
.ok-msg { display: inline-flex; align-items: center; gap: 7px; background: #e7f4ee; color: #0b7a52;
  border: 1px solid #cfe6da; border-radius: 8px; padding: 9px 12px; font-size: 13.5px; font-weight: 600; }
</style>
