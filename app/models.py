from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class InvoiceRequest(BaseModel):
    url: str = Field(
        min_length=10,
        max_length=2048,
        examples=[
            "https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce?p=43261094896792000178650040008204001431727161|2|1|1|E0286CD0069DA6018A9F8114036C1D788898DBA6"
        ],
    )


class Issuer(BaseModel):
    name: str | None = None
    cnpj: str | None = None
    address: str | None = None


class Product(BaseModel):
    name: str
    code: str | None = None
    quantity: Decimal
    unit: str | None = None
    unit_price: Decimal | None = None
    total_price: Decimal


class Payment(BaseModel):
    method: str
    amount: Decimal


class Invoice(BaseModel):
    access_key: str | None = None
    number: str | None = None
    series: str | None = None
    issued_at: datetime | None = None
    issuer: Issuer
    products: list[Product]
    total_items: int | None = None
    total_amount: Decimal | None = None
    payments: list[Payment] = []
    approximate_taxes: Decimal | None = None
