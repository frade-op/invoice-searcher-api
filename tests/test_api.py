from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from app.main import app, get_http
from app.parser import ParseError, parse_nfce

HTML = (Path(__file__).parent / "fixtures" / "svrs.html").read_text(encoding="utf-8")
URL = "https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce?p=4326|2|1|1|ABC"


def test_parse_fixture():
    inv = parse_nfce(HTML)
    assert len(inv.products) == 8 == inv.total_items
    first = inv.products[0]
    assert (first.name, first.code, first.unit) == ("COCA COLA 2L ZERO", "115000", "UN")
    assert first.unit_price == Decimal("11.98")
    assert inv.products[1].quantity == Decimal("0.115")
    assert inv.total_amount == Decimal("67.05")
    assert sum(p.total_price for p in inv.products) == inv.total_amount
    assert [p.amount for p in inv.payments] == [Decimal("33.52"), Decimal("33.53")]
    assert inv.issuer.cnpj == "94.896.792/0001-78"
    assert inv.access_key == "43261094896792000178650040008204001431727161"
    assert inv.number == "820400" and inv.series == "4"
    assert inv.issued_at.year == 2026


def test_parse_unknown_layout():
    with pytest.raises(ParseError):
        parse_nfce("<html></html>")


@pytest.fixture
async def client():
    transport = httpx.MockTransport(lambda r: httpx.Response(200, content=HTML.encode()))
    async with httpx.AsyncClient(transport=transport) as http:
        app.dependency_overrides[get_http] = lambda: http
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://t"
        ) as c:
            yield c
    app.dependency_overrides.clear()


async def test_endpoint_ok(client):
    r = await client.post("/invoices/parse", json={"url": URL})
    assert r.status_code == 200
    assert len(r.json()["products"]) == 8


@pytest.mark.parametrize(
    "url",
    ["http://dfe-portal.svrs.rs.gov.br/x", "https://evil.com/x", "https://x.gov.br.evil.com/"],
)
async def test_endpoint_rejects_bad_urls(client, url):
    r = await client.post("/invoices/parse", json={"url": url})
    assert r.status_code == 422
