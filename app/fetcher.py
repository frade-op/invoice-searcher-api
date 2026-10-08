from urllib.parse import urljoin, urlsplit

import httpx

MAX_BYTES = 2_000_000


class InvalidUrlError(ValueError):
    pass


class UpstreamError(Exception):
    pass


def validate_url(url: str) -> str:
    """Evita SSRF: só aceita HTTPS em domínios oficiais *.gov.br."""
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or not host.endswith(".gov.br"):
        raise InvalidUrlError("A URL deve ser HTTPS e de um domínio .gov.br (SEFAZ).")
    if parts.port not in (None, 443) or parts.username or parts.password:
        raise InvalidUrlError("URL inválida.")
    return parts.geturl()


async def fetch_html(client: httpx.AsyncClient, url: str) -> str:
    try:
        # Redirecionamentos são seguidos manualmente para revalidar cada destino.
        for _ in range(4):
            resp = await client.get(url, follow_redirects=False)
            if resp.is_redirect:
                url = validate_url(urljoin(url, resp.headers.get("location", "")))
                continue
            resp.raise_for_status()
            if len(resp.content) > MAX_BYTES:
                raise UpstreamError("Resposta da SEFAZ grande demais.")
            return resp.content.decode("utf-8", errors="replace")
        raise UpstreamError("Redirecionamentos demais.")
    except httpx.HTTPError as exc:
        raise UpstreamError(f"Falha ao consultar a SEFAZ: {exc.__class__.__name__}") from exc
