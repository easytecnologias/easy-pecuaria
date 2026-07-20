/**
 * Tour guiado dentro do proprio sistema.
 *
 * Em vez de um video que desatualiza, o passo a passo acontece na tela real:
 * destaca o elemento, explica em uma frase e avanca. Cada publico tem sua
 * trilha, porque quem anota pesagem no curral nao precisa saber de duplicata.
 *
 * `alvo` e um seletor CSS. Se o elemento nao existir (tela sem dado ainda, ou
 * menu escondido no celular), o passo aparece centralizado em vez de sumir.
 */
import { ref } from "vue";

export interface PassoTour {
  rota?: string;      // navega para ca antes de mostrar o passo
  alvo?: string;      // seletor do elemento a destacar
  titulo: string;
  texto: string;
}

export interface Trilha {
  id: string;
  nome: string;
  emoji: string;
  publico: string;
  duracao: string;
  passos: PassoTour[];
}

const FIM = {
  titulo: "É isso!",
  texto:
    "Você pode refazer este passo a passo quando quiser, em \"Como funciona\" no menu. " +
    "Se algo não estiver claro, fale com quem cuida do sistema.",
};

export const TRILHAS: Trilha[] = [
  {
    id: "campo",
    nome: "Quem anota no dia a dia",
    emoji: "🐂",
    publico: "Equipe da fazenda",
    duracao: "1 min",
    passos: [
      {
        rota: "/painel",
        titulo: "Bem-vindo",
        texto:
          "Vou te mostrar em 1 minuto o que você precisa para o dia a dia. " +
          "Pode ir avançando — nada do que aparecer aqui altera dado nenhum.",
      },
      {
        rota: "/campo",
        alvo: ".nav__item[href='/campo']",
        titulo: "Modo campo",
        texto:
          "Esta é a tela para usar no curral, pelo celular. Letras grandes e poucos botões. " +
          "Se o sinal cair, o que você digitar fica guardado e sobe sozinho quando a internet voltar.",
      },
      {
        rota: "/campo",
        alvo: ".salvar",
        titulo: "Pesar é só isso",
        texto:
          "Escolhe o animal, digita o peso e salva. O sistema calcula o ganho por dia sozinho — " +
          "você não precisa fazer conta nenhuma.",
      },
      {
        rota: "/registrar",
        alvo: "h1",
        titulo: "Anotar qualquer coisa",
        texto:
          "Aqui ficam as outras anotações: vacina, parto, desmame, morte, venda. " +
          "Escolha o que aconteceu e o sistema pergunta só o necessário.",
      },
      {
        rota: "/movimentacao",
        alvo: ".panel",
        titulo: "Mover animal de lugar",
        texto:
          "Toda movimentação guarda quem fez e quando. Isso não é fiscalização: " +
          "é para conseguir achar o erro depois, quando um número não bater.",
      },
      { ...FIM },
    ],
  },
  {
    id: "direcao",
    nome: "Quem acompanha os números",
    emoji: "📊",
    publico: "Direção",
    duracao: "1 min",
    passos: [
      {
        rota: "/painel",
        alvo: ".metrics",
        titulo: "Visão consolidada",
        texto:
          "O painel junta as três fazendas. Estes números vêm do que a equipe anota — " +
          "ninguém digita relatório, o número se monta sozinho.",
      },
      {
        rota: "/painel",
        alvo: ".panel",
        titulo: "Fazenda por fazenda",
        texto:
          "Abaixo, cada fazenda com seus indicadores. As que têm mais alertas aparecem primeiro, " +
          "para o problema não ficar escondido no fim da lista.",
      },
      {
        rota: "/alertas",
        alvo: ".nav__item[href='/alertas']",
        titulo: "O que precisa de você",
        texto:
          "Quando um indicador sai da meta, vira alerta aqui. É a lista do que merece decisão, " +
          "em vez de você ter que caçar o problema.",
      },
      {
        rota: "/planejamento",
        alvo: ".panel",
        titulo: "Mandar fazer e acompanhar",
        texto:
          "Lance a atividade, defina o responsável e o prazo. A pessoa vê em \"Minhas pendentes\" " +
          "e marca como concluída — e você acompanha a taxa de conclusão.",
      },
      {
        rota: "/metas",
        alvo: ".panel",
        titulo: "As metas são suas",
        texto:
          "Os alertas usam estas metas. Se a meta não refletir a realidade da fazenda, " +
          "mude aqui — o sistema passa a cobrar pelo número novo.",
      },
      { ...FIM },
    ],
  },
  {
    id: "financeiro",
    nome: "Contas e vencimentos",
    emoji: "🧾",
    publico: "Financeiro",
    duracao: "1 min",
    passos: [
      {
        rota: "/contas",
        alvo: ".metrics",
        titulo: "A pagar e a receber",
        texto:
          "O topo mostra quanto está em aberto dos dois lados e o saldo previsto. " +
          "É o compromisso — não é o que já saiu do caixa.",
      },
      {
        rota: "/contas",
        alvo: ".aviso",
        titulo: "O que está vencendo",
        texto:
          "Esta faixa junta o que já venceu e o que vence em até 7 dias. " +
          "Se ela não aparecer, é porque não há nada atrasado ou próximo.",
      },
      {
        rota: "/contas",
        alvo: ".panel",
        titulo: "Lançar a duplicata",
        texto:
          "Em \"A pagar\" ou \"A receber\" você registra o documento com o vencimento. " +
          "Duplicata, boleto, nota ou recibo — com número e fornecedor.",
      },
      {
        rota: "/contas",
        alvo: ".acoes",
        titulo: "Dar baixa",
        texto:
          "Quando pagar ou receber, clique em Baixar. Dá para ajustar o valor se houve juros " +
          "ou desconto — o sistema registra o que de fato aconteceu.",
      },
      {
        rota: "/financeiro",
        alvo: ".metrics",
        titulo: "A baixa cai aqui",
        texto:
          "Ao dar baixa, o valor entra no caixa automaticamente: despesa se era a pagar, " +
          "receita se era a receber. Você não lança a mesma coisa duas vezes.",
      },
      { ...FIM },
    ],
  },
];

// --- estado compartilhado (AjudaView inicia, AppShell exibe) ----------------
const CHAVE_VISTO = "pecuaria:tour-visto";

export const trilhaAtiva = ref<Trilha | null>(null);
export const passoAtual = ref(0);

export function iniciarTour(id: string) {
  const t = TRILHAS.find((x) => x.id === id);
  if (!t) return;
  trilhaAtiva.value = t;
  passoAtual.value = 0;
}

export function fecharTour() {
  trilhaAtiva.value = null;
  passoAtual.value = 0;
  localStorage.setItem(CHAVE_VISTO, "1");
}

export function jaViuTour(): boolean {
  return localStorage.getItem(CHAVE_VISTO) === "1";
}

/** Trilha sugerida pelo papel do usuario, para o primeiro acesso. */
export function trilhaDoPapel(papel: string): string {
  if (papel === "admin" || papel === "direcao") return "direcao";
  if (papel === "financeiro") return "financeiro";
  return "campo";
}
