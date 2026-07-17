// Cliente de API tipado — padrao SightOps consome estes tipos direto.
const BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export type Severidade = "OK" | "REVISAR" | "AVALIAR" | "ALERTA" | "CRITICO";
export type Formato = "numero" | "percentual" | "moeda" | "dias";

export interface IndicadorPainel {
  codigo: string;
  nome: string;
  categoria: string | null;
  unidade: string | null;
  formato: Formato;
  casas_decimais: number;
  valor: number | null;
  data_ref: string | null;
  situacao: Severidade;
  referencia: number | null;
  acao: string | null;
}

export interface FazendaPainel {
  id: string;
  nome: string;
  municipio: string | null;
  uf: string | null;
  alertas_abertos: number;
  por_severidade: Record<string, number>;
  indicadores: IndicadorPainel[];
}

export interface Dashboard {
  organizacao: string;
  resumo: { fazendas: number; alertas_abertos: number; por_severidade: Record<string, number> };
  fazendas: FazendaPainel[];
}

export interface Fazenda {
  id: string;
  nome: string;
  municipio: string | null;
  uf: string | null;
  ativo: boolean;
}

export interface Alerta {
  id: string;
  fazenda_id: string;
  indicador_id: string;
  severidade: Severidade;
  status: string;
  valor_observado: number | null;
  valor_referencia: number | null;
  mensagem: string;
  acao: string | null;
  avaliado_em: string;
  resolvido_em: string | null;
}

export interface Parametro {
  id: string;
  grupo: string | null;
  chave: string;
  rotulo: string;
  valor: number;
  unidade: string | null;
}

export interface Usuario {
  id: string;
  nome: string;
  email: string;
  papel: string;
  is_superadmin?: boolean;
}

export interface SeriePonto {
  data_ref: string;
  valor: number;
}

const TOKEN_KEY = "pecuaria_token";
export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t: string) => localStorage.setItem(TOKEN_KEY, t);
// cache do usuário logado + throttle do refresh (evita chamadas a cada navegação)
let _meCache: Usuario | null = null;
let _lastRefresh = 0;
export const clearToken = () => { localStorage.removeItem(TOKEN_KEY); _meCache = null; _lastRefresh = 0; invalidarFazendas(); };

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (res.status === 401) {
    clearToken();
    throw new Error("Sessão expirada");
  }
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j?.detail) msg = j.detail;
    } catch { /* sem corpo */ }
    throw new Error(msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function login(email: string, senha: string): Promise<void> {
  const body = new URLSearchParams({ username: email, password: senha });
  const res = await fetch(`${BASE}/auth/login`, { method: "POST", body });
  if (!res.ok) throw new Error("Email ou senha inválidos");
  const data = (await res.json()) as { access_token: string };
  setToken(data.access_token);
  _meCache = null; _lastRefresh = Date.now(); invalidarFazendas();  // novo login: reseta caches
}

export const me = () => req<Usuario>("/auth/me");
// versão cacheada: busca /auth/me só uma vez por sessão (usada na navegação)
export async function getMeCached(): Promise<Usuario> {
  if (!_meCache) _meCache = await me();
  return _meCache;
}
// renova o token no máximo 1x a cada 5 min (em vez de a cada navegação)
export async function refreshTokenThrottled(): Promise<void> {
  if (Date.now() - _lastRefresh < 5 * 60 * 1000) return;
  _lastRefresh = Date.now();
  await refreshToken();
}

export const trocarMinhaSenha = (senha_atual: string, senha_nova: string) =>
  req<void>("/auth/senha", {
    method: "PUT", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ senha_atual, senha_nova }),
  });
export async function refreshToken(): Promise<void> {
  const data = await req<{ access_token: string }>("/auth/refresh", { method: "POST" });
  setToken(data.access_token);
}

export interface AuditLog {
  id: string; usuario_email: string; acao: string;
  entidade: string | null; entidade_id: string | null; detalhe: string | null; created_at: string;
}
export const getAuditoria = () => req<AuditLog[]>("/admin/auditoria");

// ---- Plataforma (super-admin: organizações/tenants) ----
export interface OrgPlataforma { id: string; nome: string; slug: string; n_fazendas: number; n_usuarios: number; }
export const getOrganizacoes = () => req<OrgPlataforma[]>("/platform/organizacoes");
export const criarOrganizacao = (body: {
  nome: string; slug: string; admin_nome: string; admin_email: string; admin_senha: string;
}) => req<OrgPlataforma>("/platform/organizacoes", {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const renomearOrganizacao = (id: string, nome: string) =>
  req<OrgPlataforma>(`/platform/organizacoes/${id}`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nome }),
  });

// ---- Administração (usuários + organização) ----
export interface UsuarioAdmin {
  id: string; nome: string; email: string; papel: string; ativo: boolean; fazenda_ids: string[];
}
export interface Organizacao { id: string; nome: string; slug: string; }
export const getUsuarios = () => req<UsuarioAdmin[]>("/admin/usuarios");
export const criarUsuario = (body: {
  nome: string; email: string; senha: string; papel: string; fazenda_ids: string[];
}) => req<UsuarioAdmin>("/admin/usuarios", {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const editarUsuario = (id: string, body: Partial<{
  nome: string; papel: string; ativo: boolean; fazenda_ids: string[];
}>) => req<UsuarioAdmin>(`/admin/usuarios/${id}`, {
  method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const resetarSenha = (id: string, senha: string) =>
  req<void>(`/admin/usuarios/${id}/senha`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ senha }),
  });
export const excluirUsuario = (id: string) => req<void>(`/admin/usuarios/${id}`, { method: "DELETE" });
export const getOrganizacao = () => req<Organizacao>("/admin/organizacao");
export const editarOrganizacao = (nome: string) =>
  req<Organizacao>("/admin/organizacao", {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nome }),
  });
export const getDashboard = () => req<Dashboard>("/dashboard");
export const getPainelFazenda = (id: string) => req<FazendaPainel>(`/dashboard/fazenda/${id}`);

export interface MesEvolucao { periodo: string; label: string; ano: string; nascimentos: number; }
export interface EvolucaoRebanho { meses: MesEvolucao[]; total_nascimentos_12m: number; total_ativos: number; }
export const getEvolucaoRebanho = () => req<EvolucaoRebanho>("/dashboard/evolucao");
// lista de fazendas cacheada (usada em quase toda tela; muda raramente).
// invalida ao criar/editar/excluir fazenda e no login/logout.
let _fazendasCache: Fazenda[] | null = null;
export function invalidarFazendas() { _fazendasCache = null; }
export async function getFazendas(): Promise<Fazenda[]> {
  if (!_fazendasCache) _fazendasCache = await req<Fazenda[]>("/fazendas");
  return _fazendasCache;
}
export const criarFazenda = (body: { nome: string; municipio?: string; uf?: string }) => {
  invalidarFazendas();
  return req<Fazenda>("/fazendas", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
};
export const atualizarFazenda = (id: string, body: { nome?: string; municipio?: string; uf?: string }) => {
  invalidarFazendas();
  return req<Fazenda>(`/fazendas/${id}`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
};
export const excluirFazenda = (id: string) => {
  invalidarFazendas();
  return req<void>(`/fazendas/${id}`, { method: "DELETE" });
};
export const getAlertas = (apenasAbertos = true) =>
  req<Alerta[]>(`/alertas?apenas_abertos=${apenasAbertos}`);
export const getParametros = (id: string) => req<Parametro[]>(`/fazendas/${id}/parametros`);

export interface Regra {
  id: string;
  nome: string;
  indicador_codigo: string;
  indicador_nome: string;
  operador: string;
  tipo_referencia: string;
  parametro_chave: string | null;
  valor_referencia: number | null;
  tolerancia: number | null;
  severidade: Severidade;
  acao: string;
}
export const getRegras = () => req<Regra[]>("/regras");
export const getSerie = (id: string, codigo: string) =>
  req<SeriePonto[]>(`/fazendas/${id}/indicadores/${codigo}/serie`);

export const updateParametro = (id: string, chave: string, valor: number) =>
  req<Parametro>(`/fazendas/${id}/parametros/${chave}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ valor }),
  });

export const lancarValor = (fazendaId: string, indicador_codigo: string, valor: number) =>
  req(`/fazendas/${fazendaId}/indicadores/valores`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ indicador_codigo, valor }),
  });

// ---- Rebanho ----
export interface Lote {
  id: string;
  nome: string;
  categoria: string | null;
  local: string | null;
  ativo: boolean;
  n_animais: number;
}

export interface Animal {
  id: string;
  fazenda_id: string;
  lote_id: string | null;
  brinco: string;
  categoria: string | null;
  raca: string | null;
  sexo: string | null;
  data_nascimento: string | null;
  mae_brinco: string | null;
  pai: string | null;
  origem: string | null;
  status: string;
}

export interface Pesagem {
  id: string;
  data: string;
  peso: number;
  gmd: number | null;
  observacao: string | null;
}

export interface EventoSanitario { id: string; tipo: string; produto: string; data: string; proxima_aplicacao: string | null; dose: string | null; observacao: string | null; }
export interface MovimentoFicha { id: string; tipo: string; data: string; valor: number | null; motivo: string | null; }
export interface FichaAnimal {
  animal: Animal;
  peso_atual: number | null;
  gmd_atual: number | null;
  pesagens: Pesagem[];
  inseminacoes: Inseminacao[];
  sanitarios: EventoSanitario[];
  movimentos: MovimentoFicha[];
}

export const getLotes = (fazendaId: string) => req<Lote[]>(`/fazendas/${fazendaId}/lotes`);

export const criarLote = (fazendaId: string, body: { nome: string; categoria?: string; local?: string }) =>
  req<Lote>(`/fazendas/${fazendaId}/lotes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const atualizarLote = (
  fazendaId: string,
  loteId: string,
  body: { nome?: string; categoria?: string; local?: string }
) =>
  req<Lote>(`/fazendas/${fazendaId}/lotes/${loteId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const excluirLote = (fazendaId: string, loteId: string) =>
  req<void>(`/fazendas/${fazendaId}/lotes/${loteId}`, { method: "DELETE" });

export const criarAnimal = (
  fazendaId: string,
  body: {
    brinco: string; lote_id?: string | null; categoria?: string; raca?: string;
    sexo?: string; data_nascimento?: string | null; mae_brinco?: string; pai?: string; origem?: string;
  }
) =>
  req<Animal>(`/fazendas/${fazendaId}/animais`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
export const getAnimais = (fazendaId: string, loteId?: string) =>
  req<Animal[]>(`/fazendas/${fazendaId}/animais${loteId ? `?lote_id=${loteId}` : ""}`);
export const getFicha = (animalId: string) => req<FichaAnimal>(`/animais/${animalId}`);

export const atualizarAnimal = (
  animalId: string,
  body: Partial<{
    brinco: string; lote_id: string | null; categoria: string; raca: string;
    sexo: string; data_nascimento: string | null; mae_brinco: string; pai: string; status: string;
  }>
) =>
  req<Animal>(`/animais/${animalId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const excluirAnimal = (animalId: string) =>
  req<void>(`/animais/${animalId}`, { method: "DELETE" });
export const lancarPesagem = (animalId: string, peso: number, data?: string) =>
  req<FichaAnimal>(`/animais/${animalId}/pesagens`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ peso, data }),
  });

// ---- Reprodução ----
export interface Inseminacao {
  id: string;
  animal_id: string;
  animal_brinco: string;
  data: string;
  touro: string;
  inseminador: string | null;
  protocolo: string | null;
  resultado: "pendente" | "prenhe" | "vazia";
  dg_data: string | null;
}
export interface GrupoReproducao {
  nome: string; total: number; prenhes: number; vazias: number; taxa: number | null;
}
export interface ResumoReproducao {
  total: number; prenhes: number; vazias: number; pendentes: number;
  taxa_prenhez: number | null;
  por_touro: GrupoReproducao[];
  por_inseminador: GrupoReproducao[];
  inseminacoes: Inseminacao[];
}

export const getReproducao = (fazendaId: string) =>
  req<ResumoReproducao>(`/fazendas/${fazendaId}/reproducao`);
export const criarInseminacao = (
  fazendaId: string,
  body: { animal_id: string; touro: string; data?: string; inseminador?: string; protocolo?: string }
) => req<Inseminacao>(`/fazendas/${fazendaId}/inseminacoes`, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const registrarDG = (insId: string, resultado: "prenhe" | "vazia", dg_data?: string) =>
  req<Inseminacao>(`/inseminacoes/${insId}/dg`, {
    method: "PUT", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resultado, dg_data }),
  });
export const excluirInseminacao = (insId: string) =>
  req<void>(`/inseminacoes/${insId}`, { method: "DELETE" });

// ---- Estoque de volumoso ----
export interface Movimento {
  id: string; data: string; tipo: "entrada" | "saida"; quantidade_t: number; descricao: string | null;
}
export interface ResumoEstoque {
  saldo_t: number; consumo_diario_t: number | null; dias: number | null; movimentos: Movimento[];
}
export const getEstoque = (fazendaId: string) => req<ResumoEstoque>(`/fazendas/${fazendaId}/estoque`);
export const criarMovimento = (
  fazendaId: string,
  body: { tipo: "entrada" | "saida"; quantidade_t: number; data?: string; descricao?: string }
) => req<Movimento>(`/fazendas/${fazendaId}/estoque/movimentos`, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const excluirMovimento = (id: string) =>
  req<void>(`/estoque/movimentos/${id}`, { method: "DELETE" });

// ---- Financeiro ----
export interface Lancamento {
  id: string; data: string; tipo: "despesa" | "receita"; categoria: string; valor: number; descricao: string | null;
}
export interface CategoriaFinanceira { tipo: string; categoria: string; total: number; }
export interface ResumoFinanceiro {
  receitas: number; despesas: number; saldo: number; n_animais: number;
  margem_cab: number | null; capital_giro_dias: number | null;
  categorias: CategoriaFinanceira[]; lancamentos: Lancamento[];
}
export interface PesagemRelItem { brinco: string; categoria: string | null; lote: string | null; peso: number; data: string; gmd: number | null; }
export interface RelatorioPesagem {
  total: number; com_pesagem: number; peso_medio: number | null; gmd_medio: number | null;
  arroba_media: number | null; animais: PesagemRelItem[];
}
export const getRelatorioPesagem = (fazendaId: string) =>
  req<RelatorioPesagem>(`/fazendas/${fazendaId}/relatorio-pesagem`);

export const getFinanceiro = (fazendaId: string) =>
  req<ResumoFinanceiro>(`/fazendas/${fazendaId}/financeiro`);
export const registrarLancamento = (
  fazendaId: string,
  body: { tipo: "despesa" | "receita"; categoria: string; valor: number; data?: string; descricao?: string }
) => req<Lancamento>(`/fazendas/${fazendaId}/financeiro/lancamentos`, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const excluirLancamento = (id: string) =>
  req<void>(`/financeiro/lancamentos/${id}`, { method: "DELETE" });

// ---- Escore corporal (ECC) ----
export interface EscoreHist {
  id: string; animal_id: string; brinco: string; categoria: string | null;
  data: string; escore: number; observacao: string | null;
}
export interface ResumoEscore {
  n_avaliados: number; media: number | null; magras: number; ideais: number;
  gordas: number; pct_ideais: number | null; historico: EscoreHist[];
}
export const getEscore = (fazendaId: string) => req<ResumoEscore>(`/fazendas/${fazendaId}/escore`);
export const registrarEscore = (
  fazendaId: string,
  body: { animal_id: string; escore: number; data?: string; observacao?: string }
) => req<EscoreHist>(`/fazendas/${fazendaId}/escore`, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const excluirEscore = (id: string) => req<void>(`/escore/${id}`, { method: "DELETE" });

// ---- Partos / nascimentos ----
export interface Parto {
  id: string; data: string; mae_id: string; mae_brinco: string; bezerro_id: string | null;
  resultado: "nascido_vivo" | "natimorto"; sexo_bezerro: string | null;
  brinco_bezerro: string | null; peso_nascimento: number | null; observacao: string | null;
}
export interface ResumoPartos {
  partos_12m: number; vivos_12m: number; natimortos_12m: number;
  taxa_natimortalidade: number | null; matrizes: number; taxa_natalidade: number | null;
  partos: Parto[];
}
export const getPartos = (fazendaId: string) => req<ResumoPartos>(`/fazendas/${fazendaId}/partos`);
export const registrarParto = (
  fazendaId: string,
  body: { mae_id: string; data?: string; resultado: "nascido_vivo" | "natimorto";
    sexo_bezerro?: string; brinco_bezerro?: string; peso_nascimento?: number; observacao?: string }
) => req<Parto>(`/fazendas/${fazendaId}/partos`, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const excluirParto = (id: string) => req<void>(`/partos/${id}`, { method: "DELETE" });

// ---- Nutrição / dieta ----
export interface ItemDieta {
  id?: string; ingrediente: string; inclusao_kg: number; preco_kg: number; ms_pct: number;
}
export interface Dieta {
  id: string; nome: string; lote_id: string | null; lote_nome: string | null; data: string;
  ativa: boolean; itens: ItemDieta[]; custo_cab_dia: number; consumo_ms_pv: number | null;
  kg_ms: number; peso_medio_lote: number | null;
}
export const getDietas = (fazendaId: string) => req<Dieta[]>(`/fazendas/${fazendaId}/dietas`);
export const criarDieta = (
  fazendaId: string, body: { nome: string; lote_id?: string | null; itens: ItemDieta[] }
) => req<Dieta>(`/fazendas/${fazendaId}/dietas`, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const excluirDieta = (id: string) => req<void>(`/dietas/${id}`, { method: "DELETE" });

// ---- Mercado & custos ----
export interface CotacaoArroba {
  id: string; data: string; valor: number; origem: string; fonte: string | null;
}
export interface CotacaoInsumo {
  id: string; data: string; insumo: string; praca: string | null; unidade: string;
  preco_origem: number; frete: number; outros: number; ms_pct: number;
  custo_entregue_kg: number; custo_kg_ms: number | null;
}
export interface ResumoMercado {
  arroba_atual: number | null; arroba_data: string | null;
  historico: CotacaoArroba[]; insumos: CotacaoInsumo[];
}
export interface BuscaArroba { encontrado: boolean; valor: number | null; fonte: string | null; }

export const getMercado = (fazendaId: string) => req<ResumoMercado>(`/fazendas/${fazendaId}/mercado`);
export const criarArroba = (fazendaId: string, valor: number, data?: string) =>
  req<CotacaoArroba>(`/fazendas/${fazendaId}/mercado/arroba`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ valor, data }),
  });
export const buscarArroba = (fazendaId: string) =>
  req<BuscaArroba>(`/fazendas/${fazendaId}/mercado/arroba/buscar`, { method: "POST" });
export const excluirArroba = (id: string) => req<void>(`/mercado/arroba/${id}`, { method: "DELETE" });
export const criarInsumo = (
  fazendaId: string,
  body: { insumo: string; preco_origem: number; ms_pct: number; praca?: string; unidade?: string; frete?: number; outros?: number }
) => req<CotacaoInsumo>(`/fazendas/${fazendaId}/mercado/insumos`, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const excluirInsumo = (id: string) => req<void>(`/mercado/insumos/${id}`, { method: "DELETE" });

// ---- Sanitário ----
export interface AgendaSanitaria { produto: string; tipo: string; proxima: string; animais: number; vencido: boolean; vence_proximo: boolean; }
export interface HistoricoSanitario { id: string; brinco: string; tipo: string; produto: string; data: string; proxima: string | null; dose: string | null; }
export interface ResumoSanitario { total: number; vencendo: number; agenda: AgendaSanitaria[]; historico: HistoricoSanitario[]; }
export const getSanitario = (fazendaId: string) => req<ResumoSanitario>(`/fazendas/${fazendaId}/sanitario`);
export const registrarAplicacao = (
  fazendaId: string,
  body: { tipo: string; produto: string; data?: string; proxima_aplicacao?: string | null; dose?: string; observacao?: string; animal_id?: string | null; lote_id?: string | null }
) => req(`/fazendas/${fazendaId}/sanitario/aplicacoes`, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const excluirEventoSanitario = (id: string) => req<void>(`/sanitario/${id}`, { method: "DELETE" });

// ---- Movimentação de animais ----
export interface MovimentoAnimalItem { id: string; brinco: string; tipo: string; data: string; valor: number | null; motivo: string | null; }
export interface ResumoMovimentos { vendas_30d: number; mortes_30d: number; descartes_30d: number; compras_30d: number; movimentos: MovimentoAnimalItem[]; }
export interface CategoriaComposicao { categoria: string; total: number; }
export interface ComposicaoRebanho { total: number; femeas: number; machos: number; por_categoria: CategoriaComposicao[]; }
export const getMovimentos = (fazendaId: string) => req<ResumoMovimentos>(`/fazendas/${fazendaId}/movimentos`);
export const getComposicao = (fazendaId: string) => req<ComposicaoRebanho>(`/fazendas/${fazendaId}/rebanho-composicao`);
export const registrarMovimentoAnimal = (
  animalId: string,
  body: { tipo: string; data?: string; valor?: number | null; motivo?: string; lote_destino_id?: string | null; observacao?: string }
) => req(`/animais/${animalId}/movimentos`, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const excluirMovimentoAnimal = (id: string) => req<void>(`/movimentos/${id}`, { method: "DELETE" });

// ---- helpers de formatacao ----
export function fmtValor(v: number | null, formato: Formato, casas: number): string {
  if (v === null || v === undefined) return "—";
  if (formato === "percentual") return (v * 100).toFixed(Math.max(1, casas)) + "%";
  if (formato === "moeda") return "R$ " + v.toFixed(casas);
  if (formato === "dias") return v.toFixed(0) + " d";
  return v.toFixed(casas);
}
