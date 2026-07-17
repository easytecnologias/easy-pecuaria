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

## Segredos

Nada de senha/chave/token/certificado no repositório. Tudo via `.env` (gitignored) e volumes no servidor.
