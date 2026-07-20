<script setup lang="ts">
/**
 * Overlay do tour: escurece a tela, abre um "furo" sobre o elemento do passo
 * e mostra o balao ao lado. Se o elemento nao existir ou estiver escondido
 * (menu fechado no celular, tela ainda carregando), o balao vai para o centro
 * — o tour nunca trava por causa de um seletor que nao achou.
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { X, ArrowRight, ArrowLeft } from "lucide-vue-next";
import { fecharTour, passoAtual, trilhaAtiva } from "../tour";

const router = useRouter();

const rect = ref<{ top: number; left: number; width: number; height: number } | null>(null);
const pronto = ref(false);

const passo = computed(() => trilhaAtiva.value?.passos[passoAtual.value] ?? null);
const total = computed(() => trilhaAtiva.value?.passos.length ?? 0);
const ultimo = computed(() => passoAtual.value >= total.value - 1);

const PADDING = 8;

/** Espera o elemento aparecer (a tela pode estar buscando dados ainda). */
function esperarElemento(seletor: string, limiteMs = 2500): Promise<HTMLElement | null> {
  return new Promise((resolve) => {
    const inicio = Date.now();
    const tenta = () => {
      const el = document.querySelector<HTMLElement>(seletor);
      if (el && el.getBoundingClientRect().width > 0) return resolve(el);
      if (Date.now() - inicio > limiteMs) return resolve(null);
      setTimeout(tenta, 120);
    };
    tenta();
  });
}

function medir(el: HTMLElement) {
  const r = el.getBoundingClientRect();
  rect.value = { top: r.top, left: r.left, width: r.width, height: r.height };
}

async function aplicarPasso() {
  pronto.value = false;
  rect.value = null;
  const p = passo.value;
  if (!p) return;

  if (p.rota && router.currentRoute.value.path !== p.rota) {
    await router.push(p.rota).catch(() => { /* rota repetida, tudo bem */ });
  }

  if (p.alvo) {
    const el = await esperarElemento(p.alvo);
    if (el) {
      el.scrollIntoView({ block: "center", behavior: "smooth" });
      // deixa a rolagem assentar antes de medir
      await new Promise((r) => setTimeout(r, 320));
      medir(el);
    }
  }
  pronto.value = true;
}

function proximo() {
  if (ultimo.value) return fecharTour();
  passoAtual.value += 1;
}
function anterior() {
  if (passoAtual.value > 0) passoAtual.value -= 1;
}
function onTecla(e: KeyboardEvent) {
  if (!trilhaAtiva.value) return;
  if (e.key === "Escape") fecharTour();
  if (e.key === "ArrowRight" || e.key === "Enter") proximo();
  if (e.key === "ArrowLeft") anterior();
}
function remedir() {
  const p = passo.value;
  if (!p?.alvo) return;
  const el = document.querySelector<HTMLElement>(p.alvo);
  if (el) medir(el);
}

watch([trilhaAtiva, passoAtual], aplicarPasso, { immediate: true });
onMounted(() => {
  window.addEventListener("keydown", onTecla);
  window.addEventListener("resize", remedir);
  window.addEventListener("scroll", remedir, true);
});
onBeforeUnmount(() => {
  window.removeEventListener("keydown", onTecla);
  window.removeEventListener("resize", remedir);
  window.removeEventListener("scroll", remedir, true);
});

// posicao do balao: abaixo do alvo se couber, senao acima; centralizado se sem alvo
const estiloBalao = computed(() => {
  const r = rect.value;
  if (!r) return { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };
  const larguraBalao = Math.min(340, window.innerWidth - 24);
  const espacoAbaixo = window.innerHeight - (r.top + r.height);
  const abaixo = espacoAbaixo > 220;
  const left = Math.min(
    Math.max(12, r.left + r.width / 2 - larguraBalao / 2),
    window.innerWidth - larguraBalao - 12
  );
  return abaixo
    ? { top: `${r.top + r.height + PADDING + 10}px`, left: `${left}px` }
    : { top: `${Math.max(12, r.top - PADDING - 10)}px`, left: `${left}px`, transform: "translateY(-100%)" };
});

const estiloFuro = computed(() => {
  const r = rect.value;
  if (!r) return { display: "none" };
  return {
    top: `${r.top - PADDING}px`,
    left: `${r.left - PADDING}px`,
    width: `${r.width + PADDING * 2}px`,
    height: `${r.height + PADDING * 2}px`,
  };
});
</script>

<template>
  <div v-if="trilhaAtiva && passo" class="tour" role="dialog" aria-modal="true">
    <!-- sem alvo: escurece tudo. com alvo: o box-shadow gigante faz o furo -->
    <div v-if="!rect" class="tour__veu" @click="fecharTour" />
    <div v-else class="tour__furo" :style="estiloFuro" />

    <div class="balao" :style="estiloBalao" v-show="pronto">
      <button class="balao__x" @click="fecharTour" aria-label="Fechar"><X :size="16" /></button>

      <div class="balao__passo">
        {{ trilhaAtiva.emoji }} {{ passoAtual + 1 }} de {{ total }}
      </div>
      <h3>{{ passo.titulo }}</h3>
      <p>{{ passo.texto }}</p>

      <div class="barra"><div class="barra__f" :style="{ width: `${((passoAtual + 1) / total) * 100}%` }" /></div>

      <div class="balao__acoes">
        <button class="btn btn--secondary bp" v-if="passoAtual > 0" @click="anterior">
          <ArrowLeft :size="14" /> Voltar
        </button>
        <button class="btn btn--secondary bp" v-else @click="fecharTour">Pular</button>
        <button class="btn btn--primary bp" @click="proximo">
          {{ ultimo ? "Concluir" : "Próximo" }}
          <ArrowRight v-if="!ultimo" :size="14" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tour { position: fixed; inset: 0; z-index: 9000; }
.tour__veu { position: absolute; inset: 0; background: rgba(15, 23, 42, .62); }
/* o "furo": a sombra imensa escurece todo o resto da tela */
.tour__furo {
  position: fixed; border-radius: 10px; pointer-events: none;
  box-shadow: 0 0 0 9999px rgba(15, 23, 42, .62);
  outline: 2px solid var(--primary); outline-offset: 2px;
  transition: top .2s, left .2s, width .2s, height .2s;
}
.balao {
  position: fixed; width: min(340px, calc(100vw - 24px));
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 16px 16px 14px; box-shadow: 0 18px 40px rgba(15, 23, 42, .28);
}
.balao__x {
  position: absolute; top: 10px; right: 10px; border: none; background: transparent;
  color: var(--muted); cursor: pointer; padding: 2px; line-height: 0;
}
.balao__x:hover { color: var(--danger); }
.balao__passo {
  font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em;
  color: var(--muted); font-weight: 700; margin-bottom: 6px;
}
.balao h3 { font-size: 16px; margin: 0 0 6px; padding-right: 20px; }
.balao p { font-size: 13.5px; line-height: 1.5; color: var(--muted); margin: 0 0 12px; }
.barra { height: 4px; background: var(--bg); border-radius: 999px; overflow: hidden; margin-bottom: 12px; }
.barra__f { height: 100%; background: var(--primary); border-radius: 999px; transition: width .25s; }
.balao__acoes { display: flex; gap: 8px; justify-content: flex-end; }
.bp { height: 32px; padding: 0 14px; font-size: 13px; }
</style>
