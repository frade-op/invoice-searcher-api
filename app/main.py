import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.fetcher import InvalidUrlError, UpstreamError, fetch_html, validate_url
from app.models import Invoice, InvoiceRequest
from app.parser import ParseError, parse_nfce


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(15.0),
        headers={"User-Agent": "invoice-searcher-api/0.1"},
    ) as client:
        app.state.http = client
        yield


app = FastAPI(title="Invoice Searcher API", version="0.1.0", lifespan=lifespan)

_default_origins = "http://127.0.0.1:5500,http://localhost:5500"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip() for o in os.environ.get("CORS_ORIGINS", _default_origins).split(",") if o.strip()
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/invoices/parse", response_model=Invoice)
async def parse_invoice(
    body: InvoiceRequest, client: Annotated[httpx.AsyncClient, Depends(get_http)]
) -> Invoice:
    try:
        url = validate_url(body.url)
    except InvalidUrlError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        html = await fetch_html(client, url)
    except (InvalidUrlError, UpstreamError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    try:
        return parse_nfce(html)
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
