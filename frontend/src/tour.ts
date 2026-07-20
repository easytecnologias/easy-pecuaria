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

/**
 * Tour de UMA tela, para o botao "Como usar" que aparece em todas elas.
 *
 * Tres passos por tela, sempre na mesma logica: para que serve -> o que fazer
 * aqui -> onde isso reaparece depois. O terceiro passo e o que costuma faltar:
 * a pessoa anota e nao sabe que aquilo virou indicador em outro lugar.
 */
export const TOURS_TELA: Record<string, PassoTour[]> = {
  "/painel": [
    { alvo: ".metrics", titulo: "Os números do grupo", texto: "O topo junta as três fazendas. Nada aqui é digitado: tudo vem do que a equipe anota no campo." },
    { alvo: ".panel", titulo: "Fazenda por fazenda", texto: "Abaixo, cada fazenda com seus indicadores. As com mais alertas vêm primeiro, para o problema não ficar escondido." },
    { titulo: "De onde vem", texto: "Pesagem vira GMD, dieta vira custo por cabeça, lançamento vira margem. Se um número parecer errado, o caminho é conferir o lançamento que o alimenta." },
  ],
  "/alertas": [
    { alvo: ".panel", titulo: "O que saiu da meta", texto: "Cada linha é um indicador que ultrapassou a meta da fazenda. Os mais severos aparecem primeiro." },
    { titulo: "Por que apareceu", texto: "O alerta nasce da comparação entre o indicador e a meta. Se você acha que a meta está irreal, mude em Metas — o alerta acompanha." },
    { titulo: "O que fazer", texto: "Alerta não é castigo, é uma lista de decisões pendentes. Resolvido o problema no campo, ele fecha sozinho no próximo cálculo." },
  ],
  "/relatorios": [
    { alvo: ".seg", titulo: "Relatórios prontos", texto: "Escolha o tipo e a fazenda. Serve para levar em reunião ou mandar para o contador." },
    { alvo: ".btn--primary", titulo: "Gerar", texto: "Dá para imprimir, salvar em PDF ou exportar para Excel — aí você mexe na planilha do seu jeito." },
    { titulo: "Sempre atualizado", texto: "O relatório é montado na hora, com o dado de agora. Não existe versão velha guardada." },
  ],
  "/planejamento": [
    { alvo: ".metrics", titulo: "Como está o combinado", texto: "Em aberto, atrasadas, as da semana e a taxa de conclusão. É o acompanhamento do que foi mandado fazer." },
    { alvo: ".btn--primary", titulo: "Lançar atividade", texto: "Descreva a tarefa, escolha o tipo, o prazo e o responsável. A pessoa vê em \"Minhas pendentes\"." },
    { alvo: ".panel", titulo: "Concluir", texto: "Quem executou marca como concluída e pode escrever como foi. Fica registrado quem fez e quando." },
  ],
  "/rebanho": [
    { alvo: ".panel", titulo: "Os lotes", texto: "Os animais vivem em lotes — grupos de manejo. É por lote que a maior parte do trabalho acontece." },
    { titulo: "A ficha do animal", texto: "Clique num animal para abrir a ficha: histórico de peso, sanidade e movimentações dele." },
    { titulo: "Onde o dado nasce", texto: "É aqui que a pesagem vira GMD. Sem pesagem lançada, o painel não tem o que calcular." },
  ],
  "/campo": [
    { titulo: "Feito para o curral", texto: "Letras grandes, poucos botões, pensado para o celular na mão suja e no sol." },
    { alvo: ".salvar", titulo: "Pesar", texto: "Escolhe o animal, digita o peso, salva. O ganho por dia o sistema calcula sozinho." },
    { titulo: "Sem internet, funciona", texto: "Se o sinal cair, o que você digitar fica guardado no aparelho e sobe sozinho quando a internet voltar. Pode trabalhar tranquilo." },
  ],
  "/registrar": [
    { alvo: "h1", titulo: "Tudo começa aqui", texto: "É o atalho para anotar qualquer acontecimento: pesagem, vacina, parto, desmame, morte, venda." },
    { alvo: ".tipos", titulo: "Escolha o que aconteceu", texto: "Cada tipo pergunta só o necessário. Você não precisa saber em qual módulo aquilo mora." },
    { titulo: "O resto é automático", texto: "O sistema distribui o dado para o lugar certo e recalcula os indicadores afetados." },
  ],
  "/movimentacao": [
    { alvo: ".panel", titulo: "Entradas e saídas", texto: "Compra, venda, morte, descarte e transferência entre lotes. Cada movimento muda o status do animal." },
    { alvo: ".btn--primary", titulo: "Registrar", texto: "Escolha o tipo e o animal. Em transferência, informe o lote de destino." },
    { titulo: "Quem movimentou", texto: "Fica gravado quem fez e quando. Não é fiscalização: é para achar a origem quando um número não bater." },
  ],
  "/reproducao": [
    { alvo: ".panel", titulo: "IATF e prenhez", texto: "Registre a inseminação — matriz, touro e inseminador — e depois o diagnóstico de gestação." },
    { alvo: ".btn--primary", titulo: "Lançar", texto: "O importante é não deixar o DG sem lançar: é ele que fecha a conta da prenhez." },
    { titulo: "Taxa por touro", texto: "O sistema calcula a prenhez por touro. É assim que você descobre qual está funcionando e qual está lhe custando caro." },
  ],
  "/partos": [
    { alvo: ".panel", titulo: "Nascimentos", texto: "Registre o parto de cada matriz, com a data e como foi." },
    { alvo: ".btn--primary", titulo: "Lançar parto", texto: "Nascendo vivo, o bezerro entra no rebanho automaticamente, já ligado à mãe. Você não cadastra ele à parte." },
    { titulo: "Vira natalidade", texto: "Os partos abastecem a taxa de natalidade e a evolução do rebanho no painel." },
  ],
  "/desmame": [
    { alvo: ".metrics", titulo: "Peso e taxa de desmama", texto: "A média do peso à desmama e a taxa, comparadas com a meta da fazenda." },
    { alvo: ".btn--primary", titulo: "Lançar por bezerro", texto: "O peso é por bezerro, ligado à matriz pelo brinco da mãe — assim dá para saber quais vacas entregam bezerro pesado." },
    { titulo: "Serve para descarte", texto: "Matriz que desmama leve todo ano é candidata a descarte. Este número é o que sustenta essa decisão." },
  ],
  "/sanitario": [
    { alvo: ".panel", titulo: "Vacinas e tratamentos", texto: "Registre num animal ou no lote inteiro — vacina, vermífugo, tratamento." },
    { alvo: ".btn--primary", titulo: "Aplicar", texto: "Informe a data da próxima aplicação. É esse campo que monta o calendário." },
    { titulo: "Avisa o vencimento", texto: "Chegando perto da próxima dose, o sistema avisa. É o que evita perder o aprazamento da vacina." },
  ],
  "/escore": [
    { alvo: ".metrics", titulo: "Gordura de reserva", texto: "Escala de 1 a 5. O ideal é a matriz chegar na monta e no parto entre 2,5 e 3,5." },
    { alvo: ".btn--primary", titulo: "Avaliar", texto: "É avaliação visual, feita no curral. Não precisa de balança." },
    { titulo: "Por que importa", texto: "Magra emprenha menos; gorda tem parto difícil. O escore antecipa problema de prenhez antes de ele aparecer no DG." },
  ],
  "/nutricao": [
    { alvo: ".metrics", titulo: "Custo da dieta", texto: "Custo por cabeça por dia, custo médio ponderado e o total gasto por dia com alimentação." },
    { alvo: ".panel", titulo: "Quadro por dieta", texto: "Clique numa dieta para ver quanto cada insumo pesa no custo, do que mais custa para o que menos custa." },
    { alvo: ".btn--primary", titulo: "Montar dieta", texto: "Informe cada ingrediente com inclusão (kg), preço e matéria seca. O custo sai da conta desses itens." },
  ],
  "/estoque": [
    { alvo: ".metrics", titulo: "Dias de estoque", texto: "Quanto tempo o volumoso ainda dura no ritmo de consumo atual." },
    { alvo: ".btn--primary", titulo: "Entradas e saídas", texto: "Entrada é ensilagem ou compra; saída é o consumo do cocho. O saldo sai da diferença." },
    { titulo: "Vira alerta", texto: "Se os dias caírem abaixo da margem de segurança, o sistema avisa — com tempo de plantar ou comprar." },
  ],
  "/silagem": [
    { alvo: ".metrics", titulo: "Qualidade do silo", texto: "Total produzido, matéria seca média contra o alvo e os dias estimados de silagem." },
    { alvo: ".btn--primary", titulo: "Cadastrar silo", texto: "Cada silo com tipo, matéria seca, umidade, temperatura, o maquinário da colheita e o destino." },
    { alvo: ".panel", titulo: "Os dois avisos", texto: "Matéria seca fora do alvo significa risco de perda no silo. E quando o volume encosta no estoque de segurança, a tela avisa que é hora de repor." },
  ],
  "/financeiro": [
    { alvo: ".metrics", titulo: "Caixa de verdade", texto: "Saldo, margem por cabeça e capital de giro em dias. É o dinheiro que já entrou ou saiu." },
    { alvo: ".btn--primary", titulo: "Lançar", texto: "Despesa ou receita, com categoria. A categoria é o que permite ver depois onde o dinheiro está indo." },
    { titulo: "Contas é outra tela", texto: "Aqui é o realizado. O que ainda vai vencer fica em Contas a pagar/receber — e cai aqui sozinho quando você dá baixa." },
  ],
  "/contas": [
    { alvo: ".metrics", titulo: "O previsto", texto: "Quanto está em aberto para pagar e para receber, e o saldo previsto entre os dois." },
    { alvo: ".btn--primary", titulo: "Lançar documento", texto: "Duplicata, boleto, nota ou recibo — com número, fornecedor e vencimento." },
    { alvo: ".acoes", titulo: "Dar baixa", texto: "Pagou ou recebeu, clique em Baixar. Dá para ajustar o valor se teve juros ou desconto, e o valor entra no caixa do Financeiro." },
  ],
  "/mercado": [
    { alvo: ".panel", titulo: "Arroba e insumos", texto: "Registre a cotação do boi gordo e os preços dos insumos que você compra." },
    { alvo: ".btn--primary", titulo: "Lançar cotação", texto: "A busca automática é tentativa — a fonte externa é instável. A cotação que você digita é a base confiável." },
    { titulo: "Para que serve", texto: "A arroba entra no cálculo do valor do rebanho; o preço do insumo, no custo por kg de matéria seca." },
  ],
  "/fazendas": [
    { alvo: ".panel", titulo: "As fazendas", texto: "Cadastro das fazendas do grupo. Clique numa para ver o detalhe." },
    { alvo: ".btn--primary", titulo: "Nova fazenda", texto: "Ela já nasce com as metas padrão — depois é só ajustar em Metas o que for diferente." },
    { titulo: "Tudo é por fazenda", texto: "Rebanho, dieta, estoque e contas ficam separados por fazenda. Por isso quase toda tela tem o seletor de fazenda no topo." },
  ],
  "/inventario": [
    { alvo: ".metrics", titulo: "O patrimônio", texto: "Máquinas, equipamentos, medicações e insumos — cada um com onde está." },
    { alvo: ".btn--primary", titulo: "Cadastrar", texto: "Sempre com a localização. É ela que responde \"onde está a barra de choque\" sem telefonema." },
    { alvo: ".panel", titulo: "Mover entre fazendas", texto: "Dá para transferir de um local para outro, ou de uma fazenda para outra — e fica gravado quem moveu." },
  ],
  "/metas": [
    { alvo: ".panel", titulo: "As metas mandam", texto: "Todo alerta do sistema nasce da comparação com estes números." },
    { titulo: "Edite direto", texto: "Mude um valor e ele passa a valer na hora. Não precisa salvar em outro lugar." },
    { titulo: "Meta irreal atrapalha", texto: "Meta apertada demais gera alerta o tempo todo e a equipe para de olhar. Ajuste para a realidade da fazenda." },
  ],
  "/admin": [
    { alvo: ".panel", titulo: "Quem entra no sistema", texto: "Crie os acessos e defina o papel de cada pessoa." },
    { alvo: ".btn--primary", titulo: "Novo usuário", texto: "O papel define o que a pessoa vê; e você escolhe a quais fazendas ela tem acesso." },
    { titulo: "Cada um com o seu", texto: "Não use um login compartilhado: o sistema grava quem fez cada lançamento, e isso só serve se cada pessoa tiver o seu." },
  ],
  "/plataforma": [
    { alvo: ".panel", titulo: "Clientes da plataforma", texto: "Cada organização é um cliente independente, com dados totalmente isolados dos demais." },
    { alvo: ".btn--primary", titulo: "Nova organização", texto: "É o onboarding de um cliente novo: cria a organização e o primeiro administrador dela." },
    { titulo: "Isolamento", texto: "Um cliente nunca enxerga o dado do outro. Esta tela é só de quem administra a plataforma." },
  ],
};

/** Catalogo das telas com ajuda propria — mesma ordem e rotulo do menu. */
export const TELAS_COM_TOUR = [
  { rota: "/painel", nome: "Painel", emoji: "📊" },
  { rota: "/alertas", nome: "Alertas", emoji: "🔔" },
  { rota: "/relatorios", nome: "Relatórios", emoji: "📄" },
  { rota: "/planejamento", nome: "Planejamento", emoji: "🗓️" },
  { rota: "/rebanho", nome: "Rebanho", emoji: "🐂" },
  { rota: "/campo", nome: "Modo campo", emoji: "📴" },
  { rota: "/registrar", nome: "Registrar dados", emoji: "⚖️" },
  { rota: "/movimentacao", nome: "Movimentação", emoji: "↔️" },
  { rota: "/reproducao", nome: "Reprodução", emoji: "🧬" },
  { rota: "/partos", nome: "Partos", emoji: "🐣" },
  { rota: "/desmame", nome: "Desmame", emoji: "🍼" },
  { rota: "/sanitario", nome: "Sanitário", emoji: "💉" },
  { rota: "/escore", nome: "Escore corporal", emoji: "📏" },
  { rota: "/nutricao", nome: "Nutrição", emoji: "🥗" },
  { rota: "/estoque", nome: "Estoque", emoji: "🌽" },
  { rota: "/silagem", nome: "Silagem", emoji: "🌾" },
  { rota: "/financeiro", nome: "Financeiro", emoji: "💵" },
  { rota: "/contas", nome: "Contas a pagar/receber", emoji: "🧾" },
  { rota: "/mercado", nome: "Mercado", emoji: "💰" },
  { rota: "/fazendas", nome: "Fazendas", emoji: "🏡" },
  { rota: "/inventario", nome: "Inventário", emoji: "📦" },
  { rota: "/metas", nome: "Metas", emoji: "🎯" },
  { rota: "/admin", nome: "Administração", emoji: "⚙️" },
  { rota: "/plataforma", nome: "Organizações", emoji: "🏢" },
];

/** Monta uma trilha de uma tela so, para o botao "Como usar esta tela". */
export function trilhaDaTela(rota: string, titulo: string): Trilha | null {
  const passos = TOURS_TELA[rota];
  if (!passos) return null;
  return {
    id: `tela:${rota}`,
    nome: titulo,
    emoji: "💡",
    publico: titulo,
    duracao: "30 s",
    passos: passos.map((p) => ({ ...p, rota })),
  };
}

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

/** Inicia o tour da tela atual (botao "Como usar" da barra de cima). */
export function iniciarTourDaTela(rota: string, titulo: string) {
  const t = trilhaDaTela(rota, titulo);
  if (!t) return;
  trilhaAtiva.value = t;
  passoAtual.value = 0;
}

export function telaTemTour(rota: string): boolean {
  return rota in TOURS_TELA;
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
