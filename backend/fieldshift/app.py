"""FieldShift's local, stateless HTTP API. No network collectors run here."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import Lock

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .analysis import AnalysisService
from .demo import demo_request
from .models import CompareRequest, ContextRequest
from .repository import DataRepository, DataUnavailableError
from .validation import DocumentValidator, InvalidInput, fail

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = ROOT / "frontend" / "dist"
MAX_REQUEST_BYTES = 256 * 1024
logger = logging.getLogger("fieldshift")


def error_response(status, code, message, details=None):
    return JSONResponse(status_code=status, content={"error": {
        "code": code, "message": message, "details": details or [],
    }})


class BodyLimitMiddleware:
    def __init__(self, app, limit=MAX_REQUEST_BYTES):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                return
            body.extend(event.get("body", b""))
            if len(body) > self.limit:
                response = error_response(413, "request_too_large", "Ukuran input melebihi 256 KiB.")
                return await response(scope, receive, send)
            if not event.get("more_body", False):
                break
        delivered = False

        async def buffered_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, buffered_receive, send)


def create_app(repository=None):
    api = FastAPI(
        title="FieldShift API", version="0.1.0",
        description="Eksplorasi rotasi dengan data publik Yogyakarta–Klaten. Hasil parsial dan asumsi dinyatakan eksplisit; belum tervalidasi agronomi lokal.",
    )
    api.add_middleware(BodyLimitMiddleware)
    api.add_middleware(CORSMiddleware, allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:3000", "http://127.0.0.1:3000",
    ], allow_methods=["GET", "POST"], allow_headers=["Content-Type"], allow_credentials=False)
    api.state.repository = repository
    api.state.validator = None
    runtime_lock = Lock()

    def runtime():
        with runtime_lock:
            try:
                if api.state.repository is None:
                    api.state.repository = DataRepository(ROOT)
                if api.state.validator is None:
                    api.state.validator = DocumentValidator(ROOT)
            except (OSError, json.JSONDecodeError, KeyError) as exc:
                raise DataUnavailableError("Required data or input contract is unavailable") from exc
        return api.state.repository, api.state.validator

    @api.exception_handler(RequestValidationError)
    async def transport_error(_request, exc):
        details = [{"field": ".".join(map(str, item["loc"])), "code": item["type"],
                    "message": "Tipe, nilai atau struktur input tidak valid."} for item in exc.errors()[:20]]
        return error_response(422, "invalid_input", "Periksa input yang dikirim.", details)

    @api.exception_handler(InvalidInput)
    async def document_error(_request, exc):
        return error_response(422, "invalid_input", "Periksa input yang dikirim.", exc.details)

    @api.exception_handler(DataUnavailableError)
    async def unavailable(_request, _exc):
        return error_response(503, "data_unavailable", "Paket data lokal belum tersedia atau tidak lolos pemeriksaan integritas.")

    @api.exception_handler(Exception)
    async def unexpected(_request, exc):
        logger.error("FieldShift request failed", exc_info=exc)
        return error_response(500, "internal_error", "Analisis belum dapat diproses.")

    @api.get("/health")
    def health(services=Depends(runtime)):
        return {"status": "ok", "service": "fieldshift", "version": "0.1.0",
                "data_integrity": "verified_at_load", "storage": "stateless_read_only"}

    @api.get("/api/v1/catalog")
    def catalog(services=Depends(runtime)):
        result = services[0].catalog()
        result["sources"] = services[0].sources()
        return result

    @api.get("/api/v1/locations")
    def locations(services=Depends(runtime)):
        return {"locations": services[0].locations()}

    @api.get("/api/v1/crops")
    def crops(services=Depends(runtime)):
        return {"crops": services[0].crops}

    @api.get("/api/v1/input-contract")
    def input_contract(services=Depends(runtime)):
        return {"schema": services[1].schema, "policy": {
            "omitted_or_null": "unknown", "partial_document_accepted": True,
            "public_context": "Extracted from verified local layers; submitted reference overrides are not used.",
            "geometry": "Point support only in v0.1; non-null boundaries are rejected.",
            "persistence": "No farm input is saved.",
        }}

    @api.post("/api/v1/context")
    def context(request: ContextRequest, services=Depends(runtime)):
        resolve_location(services[0], request.location.model_dump())
        return services[0].context(request.location.model_dump(),
                                   request.window.model_dump() if request.window else None,
                                   request.time_mode)

    def resolve_location(repo, location):
        try:
            return repo.resolve_location(location)
        except ValueError:
            fail("location", "inconsistent_location", "Lokasi atau koordinat analisis tidak konsisten.")

    @api.post("/api/v1/climate/monthly")
    def climate_monthly(request: ContextRequest, services=Depends(runtime)):
        location = request.location.model_dump()
        resolve_location(services[0], location)
        if request.window is None:
            fail("window", "window_required", "Periode diperlukan untuk seri iklim bulanan.")
        return services[0].monthly_climate(location, request.window.model_dump(), request.time_mode)

    def compare_request(request, services):
        repo, validator = services
        payload = validator.normalize(request)
        # The submitted farm coordinate must agree with the resolved example too.
        resolved = resolve_location(repo, payload["location"])["coordinate"]
        farm_location = payload["document"].get("farm", {}).get("location") or {}
        for axis in ("longitude", "latitude"):
            value = farm_location.get("representative_" + axis)
            if value is not None and abs(value - resolved[axis]) > 1e-9:
                fail("farm.location.representative_" + axis, "location_mismatch", "Koordinat dokumen berbeda dari lokasi analisis.")
        return AnalysisService(repo).compare(payload)

    @api.post("/api/v1/compare")
    def compare(request: CompareRequest, services=Depends(runtime)):
        return compare_request(request, services)

    @api.get("/api/v1/demo")
    def demo(services=Depends(runtime)):
        request = demo_request()
        return {"request": request, "analysis": compare_request(CompareRequest(**request), services)}

    # Optional: serve the built frontend from the same origin. API routes above keep precedence.
    if (FRONTEND_DIST / "index.html").is_file():
        api.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    return api


app = create_app()
