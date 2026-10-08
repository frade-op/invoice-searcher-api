# AGENTS.md

Guia para agentes de IA neste repositório.

## Projeto

API FastAPI (Python 3.11+) que recebe a URL do QR Code de uma NFC-e, baixa o HTML do portal SVRS e retorna os dados estruturados (emissor, produtos, pagamentos).

## Comandos

- Instalar: `pip install -e ".[dev]"`
- Rodar: `uvicorn app.main:app --reload`
- Testes: `pytest`
- Lint: `ruff check .` (linha máx. 100)

## Estrutura

- `app/main.py`: rotas e ciclo de vida do `httpx.AsyncClient`
- `app/fetcher.py`: `validate_url` (proteção contra URLs/hosts não permitidos) e `fetch_html`
- `app/parser.py`: `parse_nfce` (BeautifulSoup)
- `app/models.py`: modelos Pydantic; valores monetários usam `Decimal`
- `tests/`: pytest com `asyncio_mode = "auto"`; HTML de exemplo em `tests/fixtures/`

## Convenções

- Tipagem completa e `async` para I/O.
- Erros de domínio (`InvalidUrlError`, `UpstreamError`, `ParseError`) são convertidos em `HTTPException` em `main.py`.
- Não relaxar a validação de URL em `validate_url` (evita SSRF).
- Toda mudança de parser ou rota deve ter teste; testes não acessam a rede (usar fixtures).
- Não commitar `.env`, `.venv` ou caches.

## Skills

- `caveman` instalado em `.agents/skills/caveman` (respostas ultra-concisas).
