# Invoice Searcher API

API que extrai produtos e dados de NFC-e a partir da URL do QR Code (portal SVRS).

## Requisitos

- Python 3.11+

## Instalação

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Executando

```powershell
.venv\Scripts\python -m uvicorn app.main:app --reload
```

Com a venv ativada, `uvicorn app.main:app --reload` também funciona. Se o PowerShell bloquear o `Activate.ps1`, rode `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Documentação interativa em http://127.0.0.1:8000/docs.

## Endpoints

| Método | Rota               | Descrição                                        |
| ------ | ------------------ | ------------------------------------------------ |
| GET    | `/health`          | Verificação de saúde                             |
| POST   | `/invoices/parse`  | Recebe `{"url": "<url do QR Code>"}` e retorna a nota |

Exemplo:

```powershell
curl -X POST http://127.0.0.1:8000/invoices/parse `
  -H "Content-Type: application/json" `
  -d '{"url": "https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce?p=..."}'
```

Erros: `422` para URL inválida ou HTML não reconhecido; `502` para falha no portal de origem.

## Estrutura

```
app/
  main.py     # rotas FastAPI
  fetcher.py  # validação da URL e download do HTML
  parser.py   # parser do HTML da NFC-e
  models.py   # modelos Pydantic
tests/        # pytest (fixtures em tests/fixtures)
```

## Deploy no Heroku

Arquivos usados: `Procfile`, `.python-version` e `requirements.txt` (mantenha-o em sincronia com as dependências do `pyproject.toml`).

```powershell
heroku login
heroku git:remote -a <nome-do-app>
git push heroku main
heroku open /health
```

Também é possível conectar o repositório do GitHub na aba **Deploy** do app e ativar o deploy automático.

## Testes e lint

```powershell
pytest
ruff check .
```
