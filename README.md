---
title: MM Motors Backend
emoji: 🏎️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# MM Motors Backend

Central FastAPI backend for the MM Motors public site and admin panel.

## Scope

- Authentication and role-based access control
- Cars, users, orders, payments, and favorites
- Admin analytics
- Search, filtering, sorting, and pagination
- API versioning under `/api/v1`

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Set `DATABASE_URL` to your Supabase Postgres connection string. For persistent app servers, use the direct or session pooler URL. For serverless deployments, Supabase recommends the transaction pooler. See the official Supabase connection string docs: https://supabase.com/docs/reference/postgres/connection-strings

Copy `.env.example` to `.env` and update the Supabase credentials before running the app.

## Database migrations

Use Alembic for schema changes:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## API

- `GET /health`
- `GET /api/v1`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /api/v1/cars`
- `GET /api/v1/orders`
- `GET /api/v1/users`
- `GET /api/v1/dashboard/stats`
