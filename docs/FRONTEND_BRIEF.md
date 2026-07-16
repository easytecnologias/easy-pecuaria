# Brief de Frontend — Painel Pecuária (para a skill ops-dashboard-ui)

Documento de handoff. O backend está **pronto e rodando**; este brief descreve o que a UI
precisa construir e o contrato exato. Contrato completo em [`openapi.json`](openapi.json).

## Contexto
Sistema de gestão pecuária **multi-fazenda** (Grupo JLN, 3 fazendas). O MVP é um **painel
executivo com motor de gatilhos**: cada KPI de cada fazenda tem uma `situacao`
(OK / REVISAR / AVALIAR / ALERTA) calculada no backend contra a meta *daquela fazenda*.
A UI **não calcula regra** — só exibe `situacao`, `valor`, `referencia` (meta) e `acao`.

## Como rodar o backend (para desenvolver contra ele)
```bash
# 1) túnel SSH p/ o Postgres (deixar rodando)
plink -ssh central@10.10.12.7 -pw <senha> -N -L 127.0.0.1:5433:127.0.0.1:5433
# 2) API
cd backend && .venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```
- API base: `http://127.0.0.1:8000`  ·  Swagger: `/docs`
- CORS já libera `http://localhost:5173` e `http://127.0.0.1:5173`
- Login de teste: `admin@pecuaria.local` / `admin123`

## Autenticação
1. `POST /auth/login` — **form-urlencoded** com `username` (email) e `password`. Retorna
   `{ access_token, token_type }`.
2. Guardar o token e enviar em todas as chamadas: `Authorization: Bearer <token>`.
3. `GET /auth/me` retorna o usuário logado.

## Endpoints principais
| Método | Rota | Uso na UI |
|--------|------|-----------|
| GET | `/dashboard` | **Tela principal.** Consolidado do grupo + cartões por fazenda |
| GET | `/dashboard/fazenda/{id}` | Detalhe de uma fazenda |
| GET | `/fazendas` | Lista de fazendas (seletor) |
| GET | `/alertas?apenas_abertos=true` | Lista de alertas (mais severos primeiro) |
| GET | `/fazendas/{id}/parametros` | Metas/premissas da fazenda (tela de config) |
| PUT | `/fazendas/{id}/parametros/{chave}` | Editar uma meta (body `{ "valor": number }`) |
| POST | `/fazendas/{id}/indicadores/valores` | Lançar valor de KPI (`{indicador_codigo, valor, data_ref?}`) — reavalia gatilhos |
| GET | `/fazendas/{id}/indicadores/{codigo}/serie` | Série temporal p/ gráfico de tendência |
| GET | `/indicadores` | Catálogo de KPIs |

## Shape do `/dashboard` (o mais importante)
```jsonc
{
  "organizacao": "Grupo JLN",
  "resumo": { "fazendas": 3, "alertas_abertos": 7,
              "por_severidade": { "ALERTA": 4, "REVISAR": 2, "AVALIAR": 1 } },
  "fazendas": [
    {
      "id": "uuid", "nome": "Fazenda Sede - Arapiraca", "municipio": "Arapiraca", "uf": "AL",
      "alertas_abertos": 4,
      "por_severidade": { "ALERTA": 2, "AVALIAR": 1, "REVISAR": 1 },
      "indicadores": [
        {
          "codigo": "custo_dieta_cab_dia", "nome": "Custo da dieta", "categoria": "Dieta",
          "unidade": "R$/cab/dia", "formato": "moeda", "casas_decimais": 2,
          "valor": 14.2, "data_ref": "2026-07-13",
          "situacao": "ALERTA", "referencia": 13.5,
          "acao": "Revisar ingredientes e preço entregue (frete, perdas, impostos)."
        }
        // ... 1 por indicador
      ]
    }
  ]
}
```

## Telas do MVP
1. **Login** — email/senha → guarda token.
2. **Dashboard (grupo)** — barra de resumo (nº fazendas, total de alertas, chips por severidade)
   + **grid de cartões por fazenda**; cada cartão lista os KPIs com badge de `situacao`, o valor
   formatado e a meta. Ordenar fazendas por nº de alertas (mais crítica primeiro).
3. **Detalhe da fazenda** — mesmos KPIs + a `acao` recomendada quando `situacao != OK` +
   gráfico de tendência (usar `/serie`) + botão "lançar valor".
4. **Alertas** — lista consolidada (`/alertas`), agrupável por fazenda/severidade.
5. **Configurações da fazenda** — editar metas (`/parametros`).

## Linguagem visual
- **Cores por severidade:** OK = verde · REVISAR = âmbar · AVALIAR = azul · ALERTA/CRITICO = vermelho.
- **Formatação por `formato`:** `percentual` → valor×100 + "%"; `moeda` → "R$ x"; `dias` → "x d";
  `numero` → `casas_decimais`.
- pt-BR, mobile-friendly (o mesmo painel será base do app de campo).

## Ponto de partida já pronto
`frontend/src/api.ts` — cliente tipado (login, getDashboard, lancarValor) com os tipos
`Dashboard`, `FazendaPainel`, `IndicadorPainel`. `frontend/src/App.vue` tem um dashboard
funcional simples que pode servir de referência ou ser substituído pela skill.
