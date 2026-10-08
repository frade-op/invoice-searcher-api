import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup, Tag

from app.models import Invoice, Issuer, Payment, Product


class ParseError(Exception):
    pass


def _text(node: Tag | None) -> str:
    return re.sub(r"\s+", " ", node.get_text(" ")).strip() if node else ""


def _money(value: str | None) -> Decimal | None:
    if not value:
        return None
    cleaned = re.sub(r"[^\d,.-]", "", value).replace(".", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _after_label(node: Tag | None) -> str:
    """Texto que segue o <strong>rótulo</strong> dentro do elemento."""
    if not node:
        return ""
    label = _text(node.find("strong"))
    return _text(node).removeprefix(label).strip()


def _find_labeled(soup: BeautifulSoup, label: str) -> str | None:
    strong = soup.find("strong", string=re.compile(rf"^\s*{label}"))
    if not strong:
        return None
    sibling = strong.next_sibling
    return re.sub(r"\s+", " ", str(sibling)).strip() if sibling else None


def _parse_product(row: Tag) -> Product | None:
    name = _text(row.select_one(".txtTit"))
    total = _money(_text(row.select_one(".valor")))
    qty = _money(_after_label(row.select_one(".Rqtd")))
    if not name or total is None or qty is None:
        return None
    code = re.search(r"digo:\s*(\S+)\s*\)", _text(row.select_one(".RCod")))
    return Product(
        name=name,
        code=code.group(1) if code else None,
        quantity=qty,
        unit=_after_label(row.select_one(".RUN")) or None,
        unit_price=_money(_after_label(row.select_one(".RvlUnit"))),
        total_price=total,
    )


def parse_nfce(html: str) -> Invoice:
    soup = BeautifulSoup(html, "html.parser")

    products = [p for r in soup.select("#tabResult tr") if (p := _parse_product(r))]
    if not products:
        raise ParseError("Nenhum produto encontrado; layout da nota não reconhecido.")

    header = soup.select_one("#conteudo")
    texts = header.select(".txtCenter .text") if header else []
    cnpj = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", _text(texts[0]) if texts else "")
    address = _text(texts[1]) if len(texts) > 1 else ""
    issuer = Issuer(
        name=_text(soup.select_one(".txtTopo")) or None,
        cnpj=cnpj.group(0) if cnpj else None,
        address=re.sub(r"\s*,\s*", ", ", address) or None,
    )

    issued_at = None
    if issued_raw := _find_labeled(soup, "Emissão"):
        m = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", issued_raw)
        if m:
            issued_at = datetime.strptime(m.group(0), "%d/%m/%Y %H:%M:%S")

    totals: dict[str, str] = {}
    payments: list[Payment] = []
    for line in soup.select("#totalNota #linhaTotal"):
        label, value = line.find("label"), line.find("span", class_="totalNumb")
        if not (label and value):
            continue
        if "tx" in (label.get("class") or []):
            if (amount := _money(_text(value))) is not None:
                payments.append(Payment(method=_text(label), amount=amount))
        else:
            totals[_text(label)] = _text(value)

    total_items = totals.get("Qtd. total de itens:", "")
    return Invoice(
        access_key=re.sub(r"\D", "", _text(soup.select_one(".chave"))) or None,
        number=_find_labeled(soup, "Número:"),
        series=_find_labeled(soup, "Série:"),
        issued_at=issued_at,
        issuer=issuer,
        products=products,
        total_items=int(total_items) if total_items.isdigit() else len(products),
        total_amount=_money(totals.get("Valor a pagar R$:")),
        payments=payments,
        approximate_taxes=_money(
            next((v for k, v in totals.items() if k.startswith("Informação dos Tributos")), None)
        ),
    )
