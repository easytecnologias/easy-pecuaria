<script setup lang="ts">
import { PlayCircle } from "lucide-vue-next";
import AppShell from "../components/AppShell.vue";
import Panel from "../components/Panel.vue";
import { TRILHAS, iniciarTour } from "../tour";

const passos = [
  { n: "1", titulo: "Evento (campo)", valor: "Pesagem: 470 kg", sub: "Garrotes Confinamento · hoje" },
  { n: "2", titulo: "Indicador (cálculo)", valor: "GMD 1,47 kg/dia", sub: "meta da fazenda: 1,55" },
  { n: "3", titulo: "Gatilho (regra)", valor: "1,47 < 1,55", sub: "abaixo da meta" },
  { n: "4", titulo: "Alerta", valor: "REVISAR lote", sub: "avisa o gerente", alerta: true },
];

const alimenta = [
  ["Pesagem", "Campo", "GMD, conversão"],
  ["Inseminação + DG", "Vet / Inseminador", "Taxa de prenhez"],
  ["Dieta do lote", "Nutricionista", "Custo/cab/dia"],
  ["Entrada/saída de silagem", "Gerente", "Dias de estoque"],
  ["Compra de insumo", "Compras", "Custo por kg MS"],
];
</script>

<template>
  <AppShell title="Como funciona" sub="A lógica do sistema em 1 minuto">
    <div class="head">
      <div class="eyebrow">Comece por aqui</div>
      <h1>Do dado ao alerta</h1>
      <p>É esta a ideia do sistema inteiro. A equipe anota fatos simples no campo; o sistema calcula os indicadores, compara com as metas da fazenda e avisa quando algo precisa de decisão. Você nunca digita "indicador".</p>
    </div>

    <Panel title="Passo a passo no sistema" sub="o guia acontece na tela real, destacando cada botão">
      <div class="trilhas">
        <button v-for="t in TRILHAS" :key="t.id" class="trilha" @click="iniciarTour(t.id)">
          <span class="trilha__emoji">{{ t.emoji }}</span>
          <span class="trilha__txt">
            <b>{{ t.nome }}</b>
            <span class="muted">{{ t.publico }} · {{ t.passos.length }} passos · {{ t.duracao }}</span>
          </span>
          <PlayCircle :size="20" class="trilha__play" />
        </button>
      </div>
      <p class="muted nota">
        Pode parar no meio e recomeçar quando quiser. O guia não altera nenhum dado —
        ele só mostra onde ficam as coisas.
      </p>
    </Panel>

    <Panel>
      <div class="flow">
        <template v-for="(p, i) in passos" :key="p.n">
          <div class="step" :class="{ alerta: p.alerta }">
            <div class="k">{{ p.n }} · {{ p.titulo }}</div>
            <div class="v">{{ p.valor }}</div>
            <div class="s">{{ p.sub }}</div>
          </div>
          <div class="arrow" v-if="i < passos.length - 1">→</div>
        </template>
      </div>
    </Panel>

    <div class="cols">
      <Panel title="O que a equipe anota" sub="fatos simples">
        <table>
          <thead><tr><th>Evento</th><th>Quem lança</th><th>Vira o indicador</th></tr></thead>
          <tbody>
            <tr v-for="a in alimenta" :key="a[0]"><td>{{ a[0] }}</td><td class="muted">{{ a[1] }}</td><td>{{ a[2] }}</td></tr>
          </tbody>
        </table>
      </Panel>

      <Panel title="O que a direção vê" sub="sem digitar nada">
        <div class="barline"><span>Custo dieta</span><div class="bar"><span style="width:92%;background:var(--danger)"></span></div><span class="badge ALERTA"><span class="dot" /> ALERTA</span></div>
        <div class="barline"><span>Prenhez</span><div class="bar"><span style="width:79%;background:var(--amber)"></span></div><span class="badge REVISAR"><span class="dot" /> REVISAR</span></div>
        <div class="barline"><span>Estoque silagem</span><div class="bar"><span style="width:60%;background:var(--danger)"></span></div><span class="badge ALERTA"><span class="dot" /> ALERTA</span></div>
        <div class="barline"><span>GMD</span><div class="bar"><span style="width:88%"></span></div><span class="badge OK"><span class="dot" /> OK</span></div>
        <div class="nota">✅ Esse painel é a tela <b>Painel</b>. Ele se preenche sozinho conforme a equipe registra os eventos.</div>
      </Panel>
    </div>

    <Panel title="Por onde começar no dia a dia">
      <ol class="passos">
        <li><b>Registrar</b> → cadastre seus lotes e animais (uma vez), depois lance pesagens e eventos.</li>
        <li><b>Rebanho</b> → veja seus animais organizados por lote e a ficha de cada um.</li>
        <li><b>Painel</b> → acompanhe a situação do grupo; o que estiver fora da meta vira alerta.</li>
        <li><b>Alertas</b> → a lista do que precisa de decisão, mais urgente primeiro.</li>
      </ol>
    </Panel>
  </AppShell>
</template>

<style scoped>
/* trilhas do tour guiado */
.trilhas { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px; }
.trilha {
  display: flex; align-items: center; gap: 12px; text-align: left;
  padding: 14px; border: 1px solid var(--border); border-radius: 10px;
  background: var(--surface); cursor: pointer; font: inherit; color: inherit;
  transition: border-color .15s, transform .15s;
}
.trilha:hover { border-color: var(--primary); transform: translateY(-1px); }
.trilha__emoji { font-size: 22px; }
.trilha__txt { display: flex; flex-direction: column; gap: 2px; flex: 1; }
.trilha__txt .muted { font-size: 12px; }
.trilha__play { color: var(--primary); flex-shrink: 0; }
.nota { font-size: 12.5px; margin-top: 12px; }
.flow { display: flex; align-items: stretch; gap: 10px; flex-wrap: wrap; padding: 6px 0; }
.step { flex: 1; min-width: 150px; background: #f7fafb; border: 1px solid var(--border); border-radius: 9px; padding: 12px; }
.step.alerta { background: #fdf3f3; border-color: #f0c9c9; }
.step .k { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
.step .v { font-size: 15px; font-weight: 700; margin-top: 3px; }
.step.alerta .v { color: #b91c1c; }
.step .s { font-size: 12px; color: var(--muted); margin-top: 3px; }
.arrow { display: grid; place-items: center; color: var(--primary); font-size: 20px; font-weight: 800; }

.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 16px 0; }
@media (max-width: 860px) { .cols { grid-template-columns: 1fr; } }
.barline { display: grid; grid-template-columns: 140px 1fr 96px; align-items: center; gap: 10px; padding: 7px 0; font-size: 13.5px; }
.bar { height: 9px; border-radius: 6px; background: #eef2f4; overflow: hidden; }
.bar > span { display: block; height: 100%; border-radius: 6px; background: var(--primary); }
.nota { background: #f2f8f5; border: 1px solid #cfe6da; border-radius: 8px; padding: 10px 12px; font-size: 13px; color: #245c47; margin-top: 10px; }
.passos { margin: 0; padding-left: 20px; line-height: 1.9; font-size: 14px; }
</style>
