# query_court
QueryCourt: the generator argues, the critic cross-examines, and the court rules.


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




**Confidence levels**

```text
No schema
  Syntax and safety review

Prompt-provided schema details
  Partial schema-aware review

Uploaded DDL
  Schema-aware reference validation

Sandbox database
  Schema validation plus controlled execution
```


## How to Run 
```bash
    uv run pytest
    uv run uvicorn query_court.main:app --reload
    curl http://127.0.0.1:8000/health
```