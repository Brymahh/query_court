# Query-Court
> The Generator argues, the Critic cross-examines, and the Court rules.


## Problem Statement

Teams increasingly use LLMs to generate SQL from natural-language requests, but generated queries can reference nonexistent columns, use incorrect joins, violate the requested SQL dialect, produce misleading results, or contain unsafe write operations. Existing text-to-SQL tools typically return one query without showing how it was evaluated, leaving users unable to determine what was actually checked.

Users also cannot always share their database schema because DDL may expose sensitive table names, business concepts, or internal infrastructure details. A useful SQL review system must therefore provide value both when schema metadata is available and when it is not.

## My Solution

Query-Court is a privacy-aware SQL generation and review product. A generator agent converts a plain-English request into SQL, while a critic agent evaluates the query in a visible, streamed conversation. The user selects the target SQL dialect and may optionally provide database context in one of two ways:

- Upload a DDL file.
- Include relevant tables, columns, and relationships in the prompt.

When DDL is provided, Query-Court parses it with `sqlglot`, extracts normalized schema metadata, and checks whether the generated query references valid tables and columns. When only schema details are included in the prompt, Query-Court uses them as partial context and clearly marks the resulting review as limited. When no schema information is available, the system still checks syntax, dialect compatibility, read-only safety, and dangerous SQL patterns, but does not claim that table or column references are valid.

The critic uses deterministic tools rather than relying only on model opinion. It parses the SQL, checks the selected dialect, validates read-only policy, compares references against available schema context, and optionally runs `EXPLAIN` or controlled execution against a sandbox containing synthetic data. The generator can revise its SQL based on the critique until the query is approved or a configured round limit is reached.

Users see the complete exchange: the original request, generated SQL, structured critique, revisions, validation results, and final verdict. The system reports exactly which checks passed, failed, or could not be performed, producing both the final SQL and an audit trail.

Query-Court is implemented as a Reflexion-style generator-critic workflow using LangGraph behind a FastAPI service. Events are streamed to a Next.js and TypeScript frontend over SSE. PostgreSQL stores session history and audit records. LangSmith provides tracing, and a Spider/BIRD-inspired evaluation suite measures SQL-generation and review quality in CI.



## How to Run
```bash
  uv sync
  uv run uvicorn app.main:app --reload --app-dir src
  curl http://127.0.0.1:8000/health
```

## Requirements

- Python 3.12
- `uv`
- Docker Desktop
- Git

## Local Setup

```bash
git clone https://github.com/Brymahh/query_court.git
cd query_court
cp .env_example .env
uv sync
```

The environment template contains empty Azure OpenAI values and a local Docker database URL.

## Run With Docker Compose

```bash
docker compose up --build -d
docker compose ps
curl http://127.0.0.1:8000/health
docker compose exec db pg_isready -U query_court -d query_court
```

Check PostgreSQL through the application container:

```bash
docker compose exec app python -c 'import os, psycopg; connection = psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3); connection.execute("SELECT 1"); print("Application database connection successful"); connection.close()'
```

Stop the local stack:

```bash
docker compose down
```

Note
- Use `docker compose down --volumes` only when you deliberately want to remove the local PostgreSQL data volume.

## Review Modes

Schema context is optional. Query-Court must never claim to have performed a check for which it had no evidence.

| Context | Checks available | Limitations |
| --- | --- | --- |
| No schema | Syntax, selected dialect, read-only policy, dangerous patterns | Cannot verify tables, columns, joins, or results |
| Prompt-provided details | No-schema checks plus partial reference checks | User-provided details are incomplete and unverified |
| Uploaded DDL | Normalized tables, columns, types, and relationships | DDL describes structure, not business meaning or real data |
| Isolated sandbox | Schema checks, `EXPLAIN`, and controlled read-only execution | Synthetic data cannot prove real business correctness |


## Architecture

See [diagram.html](diagram.html) for the architecture map.

```text
Docker Compose
|- FastAPI application container, built from Dockerfile
`- PostgreSQL 16 container for sessions and audit history
```

The planned hosted runtime is:

```text
Vercel -> Next.js frontend
Azure Container Apps -> FastAPI Docker image
Azure Database for PostgreSQL -> managed application database
```

The local PostgreSQL container is not transferred to Azure. It is replaced by the managed Azure database, while the application image remains portable.

## Development Checks

```bash
uv run pre-commit install
uv run pre-commit run --all-files
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

GitHub Actions runs these quality checks and Gitleaks secret scanning on issue and phase branch pushes and pull requests.

## Security Boundaries

- Local PostgreSQL credentials are development-only values.
- `.env` is ignored and must never be committed.
- `.dockerignore` excludes local secrets and development artifacts from the build context.
- The Dockerfile does not contain API keys or database passwords.
- PostgreSQL is a separate service from the application image.
- Production secrets will come from Azure Key Vault or managed environment configuration.
- Phase 0 does not connect to a user's production database.
- Future SQL execution will use read-only permissions, timeouts, resource limits, and an isolated sandbox.
- Synthetic sandbox results will not be presented as proof of business correctness.

## Contribution Workflow

Each issue uses its own branch and pull request into the phase branch. A phase is merged into `main` only after all of its issue pull requests and checks are
complete. Use a Conventional Commit message, keep changes within the issue, and include `Closes #N` in the pull request body. Do not commit directly to
`main`.

```text
main
`- phase/0-foundation
   |- issue/0.1-initialize-backend
   |- issue/0.2-quality-automation
   |- issue/0.3-local-infrastructure
   `- issue/0.4-documentation
```
