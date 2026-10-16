# Invoice Searcher API

API que extrai produtos e dados de NFC-e a partir da URL do QR Code.

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

## Cobertura de estados

Atualmente, a extração está implementada e testada para o layout de consulta do portal
SVRS usado no Rio Grande do Sul. O fato de a validação aceitar uma URL HTTPS em domínio
`.gov.br` não significa que o layout de outros estados seja suportado: cada portal pode
retornar HTML diferente, e a API rejeita páginas que não correspondem ao parser atual.

São Paulo (SP), Rio de Janeiro (RJ) e Rondônia (RO) ainda não têm suporte confirmado.
Para incluí-los, é necessário implementar e testar o parser com exemplos reais de cada
portal. A API aceita somente HTTPS; URLs de QR Code servidas apenas por HTTP não são
permitidas.

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
