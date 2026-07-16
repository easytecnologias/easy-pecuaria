# Pecuária — Sistema de Gestão (Grupo JLN)

Sistema de gestão pecuária **multi-fazenda** nascido do *Plano Diretor Pecuário 2026–2035*.
MVP: **painel executivo + motor de gatilhos/alertas** (a "alma" da planilha: gatilho → pior
cenário → plano B, agora vivo e com histórico).

- **Backend:** Python / FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL
- **Frontend:** Vue 3 + Vite (base mínima; UI montada com a skill Codex `ops-dashboard-ui`)
- **Infra:** Postgres em Docker no servidor `10.10.12.7` (stack `pecuaria`), acesso dev via túnel SSH

---

## Arquitetura

```
Organização (Grupo JLN)
   └── Fazenda A / B / C          (todo dado operacional carrega fazenda_id)
         ├── Parametros           (premissas/metas por fazenda — aba "Premissas")
         ├── IndicadorValor       (série temporal dos KPIs)
         └── Alerta               (gerado pelo motor de gatilhos)

RegraGatilho (da organização) --resolve limite--> Parametro da fazenda
   ex: custo_dieta > meta(custo_max_dieta) → uma regra serve as 3 fazendas
```

O **motor de gatilhos** (`app/domain/avaliacao.py` + `app/services/gatilhos.py`) reproduz as
fórmulas `=IF(...>Premissas!...)` da aba Dashboard: pega o último valor de cada indicador na
fazenda, resolve a meta **daquela fazenda** e decide a situação (OK / REVISAR / AVALIAR / ALERTA).

---

## Como rodar (dev, Windows)

### 1. Túnel SSH para o banco (Postgres roda no servidor)
```bash
# porta local 5433 -> Postgres do servidor (bind 127.0.0.1). Deixe rodando.
plink -ssh central@10.10.12.7 -pw <senha> -N -L 127.0.0.1:5433:127.0.0.1:5433
```

### 2. Backend
```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
cp .env.example .env        # ajuste DATABASE_URL/SECRET_KEY (já preenchido em dev)

# migrations + seed (só na 1ª vez)
.venv/Scripts/alembic upgrade head
.venv/Scripts/python -m app.seed.seed

# subir a API
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

- API: http://127.0.0.1:8000
- **Docs interativas (Swagger):** http://127.0.0.1:8000/docs
- Contrato: [`docs/openapi.json`](docs/openapi.json)
- Login seed: `admin@pecuaria.local` / `admin123`

### 3. Frontend (base)
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (VITE_API_URL aponta pra API)
```

---

## API (MVP)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/login` | Login (form: `username`=email, `password`). Retorna JWT. |
| GET  | `/auth/me` | Usuário logado |
| GET  | `/fazendas` | Fazendas no escopo do usuário |
| GET  | `/fazendas/{id}/parametros` | Premissas/metas da fazenda |
| PUT  | `/fazendas/{id}/parametros/{chave}` | Atualiza uma meta |
| GET  | `/dashboard` | **Consolidado do grupo + cartões por fazenda** (KPIs c/ situação) |
| GET  | `/dashboard/fazenda/{id}` | Painel de uma fazenda |
| GET  | `/alertas` | Alertas abertos no escopo (mais severos primeiro) |
| POST | `/alertas/reavaliar/{id}` | Roda o motor de gatilhos p/ a fazenda |
| GET  | `/indicadores` | Catálogo de KPIs |
| POST | `/fazendas/{id}/indicadores/valores` | Lança valor de um KPI (reavalia gatilhos) |
| GET  | `/fazendas/{id}/indicadores/{codigo}/serie` | Série temporal (gráfico de tendência) |

Todas (exceto `/auth/login` e `/health`) exigem header `Authorization: Bearer <token>`.

---

## Estrutura

```
backend/
  app/
    core/        config, db, security (JWT/bcrypt), deps (auth + escopo multi-fazenda)
    models/      SQLAlchemy (UUID PKs — preparado p/ mobile offline-first)
    schemas/     Pydantic (contrato da API)
    domain/      avaliacao.py — núcleo PURO do motor de gatilhos (testável isolado)
    services/    gatilhos.py (avaliação + alertas), painel.py (DTOs do dashboard)
    api/routers/ auth, fazendas, dashboard, alertas, indicadores
    seed/        seed.py — org + 3 fazendas + premissas + indicadores + regras (da planilha)
  alembic/       migrations
docs/            openapi.json
frontend/        Vue 3 + Vite (base p/ a skill de UI)
```

## Roadmap (próximas fases)
- Integrações automáticas: **CEPEA/B3** (arroba/BGI) e **INMET** (clima) alimentando indicadores
- Módulos operacionais: rebanho/reprodução (IATF, DG, prenhez por touro), confinamento (GMD, dieta)
- Rastreabilidade individual/lote (SISBOV), custo da @ produzida
- App mobile (Expo/React Native ou Vue/Capacitor) **offline-first** para o campo
- Deploy do stack completo (api + web) no servidor, seguindo o padrão dos demais projetos
