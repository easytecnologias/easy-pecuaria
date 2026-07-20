# Deploy

Stack em Docker Compose: **Postgres + API (FastAPI) + Web (nginx/Vue) + Cloudflare Tunnel**.

## Subir

```bash
cp .env.example .env      # e preencha as variáveis (senha, SECRET_KEY, token do túnel)
docker compose build
docker compose up -d
```

A API roda `alembic upgrade head` no boot (migrações automáticas). O primeiro seed cria a organização e o admin (`ADMIN_EMAIL` / `ADMIN_PASSWORD`).

## Acesso

- Local/LAN: `http://<servidor>:8101`
- Público (HTTPS): via **Cloudflare Tunnel** — o container `cloudflared` publica o app num domínio (ex.: `https://pecuaria.seudominio.com.br`) com certificado válido, sem abrir portas nem expor IP.
  - Crie o túnel no painel Cloudflare (**Zero Trust → Networks → Tunnels**), copie o **token** para `CLOUDFLARE_TUNNEL_TOKEN` no `.env`, e adicione um **Public Hostname** apontando para `pecuaria-web:80`.

## Backup

`deploy/backup.sh` faz `pg_dump` diário (gzip, rotação 14 dias). Agende no cron:

```
0 3 * * * /caminho/deploy/backup.sh >> /caminho/backups/backup.log 2>&1
```

## Ambientes e fluxo de trabalho

Dois ambientes no mesmo servidor, **isolados** (bancos separados):

| Ambiente | Branch | Compose | Pasta no servidor | Acesso |
|---|---|---|---|---|
| **Produção** | `main` | `docker-compose.yml` | `/home/central/pecuaria` | `https://pecuaria.easytecnologias.com.br` (Cloudflare) |
| **Homologação** | `develop` | `docker-compose.staging.yml` | `/home/central/pecuaria-staging` | `http://<servidor>:8102` (LAN) |

Fluxo: evoluir em `develop` → subir na **homologação** e testar → `merge` em `main` → subir na **produção**.

```
# HOMOLOGAÇÃO (a partir da branch develop)
#   sincroniza o codigo para /home/central/pecuaria-staging e:
cd /home/central/pecuaria-staging && docker compose up -d --build

# PRODUÇÃO (a partir da branch main, so depois de testar)
cd /home/central/pecuaria && docker compose up -d --build
```

O staging nasce com uma **cópia** do banco de produção:
```
docker exec pecuaria-postgres sh -c 'PGPASSWORD=$POSTGRES_PASSWORD pg_dump -U $POSTGRES_USER -d $POSTGRES_DB --clean --if-exists' \
  | docker exec -i pecuaria-stg-postgres sh -c 'PGPASSWORD=$POSTGRES_PASSWORD psql -q -U $POSTGRES_USER -d $POSTGRES_DB'
```

O HTTPS de produção é terminado no **Cloudflare Tunnel** (o nginx serve HTTP na 80).

## Segredos

Nada de senha/chave/token/certificado no repositório. Tudo via `.env` (gitignored) e volumes no servidor.
