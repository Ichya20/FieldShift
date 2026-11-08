"""Run backend/method checks, smoke real local HTTP, and export review artifacts."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import socket
import sys
import threading
import time
import unittest
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import uvicorn
from backend.fieldshift.app import create_app
from backend.fieldshift.repository import DataRepository


def write_json(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def smoke_http(app):
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", access_log=False))
    worker = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    worker.start()
    checks = []
    try:
        for _ in range(100):
            if server.started:
                break
            if not worker.is_alive():
                raise RuntimeError("Local smoke server failed to start")
            time.sleep(0.05)
        if not server.started:
            raise RuntimeError("Local smoke server startup timed out")

        def get(path):
            with urlopen(f"http://127.0.0.1:{port}{path}", timeout=10) as response:
                assert response.status == 200
                checks.append({"method": "GET", "path": path, "status": response.status})
                return json.load(response)

        health = get("/health")
        assert health["data_integrity"] == "verified_at_load"
        catalog = get("/api/v1/catalog")
        assert len(catalog["sources"]) > 0
        demo = get("/api/v1/demo")
        schema = get("/openapi.json")
        request = Request(f"http://127.0.0.1:{port}/api/v1/compare",
                          data=json.dumps(demo["request"], allow_nan=False).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=10) as response:
            analysis = json.load(response)
            assert response.status == 200 and analysis == demo["analysis"]
            checks.append({"method": "POST", "path": "/api/v1/compare", "status": response.status,
                           "demo_roundtrip_equal": True})
        assert [s["sequence"] for s in analysis["strategies"]] == [
            ["padi", "padi"], ["padi", "jagung"], ["padi", "kedelai"]]
        assert all(len(s["findings"]) == 12 for s in analysis["strategies"])
        assert analysis["local_agronomic_validation"] is False
        return checks, demo, schema
    finally:
        server.should_exit = True
        worker.join(timeout=5)
        sock.close()
        if worker.is_alive():
            raise RuntimeError("Local smoke server did not stop")


def main():
    results = {}
    for directory in ("method", "backend"):
        folder = str(ROOT / "tests" / directory)
        suite = unittest.TestLoader().discover(folder, pattern="test_*.py", top_level_dir=folder)
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
        print(directory + ": " + stream.getvalue().strip())
        results[directory] = {"run": result.testsRun, "failures": len(result.failures),
                              "errors": len(result.errors), "skipped": len(result.skipped)}
        if not result.wasSuccessful():
            raise SystemExit(1)
    repository = DataRepository(ROOT)
    app = create_app(repository)
    checks, demo, schema = smoke_http(app)
    write_json("outputs/backend-demo-request.json", demo["request"])
    write_json("outputs/backend-demo-response.json", demo["analysis"])
    write_json("outputs/backend-openapi.json", schema)
    write_json("outputs/backend-verification.json", {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed_backend_mvp_checks_not_local_agronomic_validation",
        "python_version": platform.python_version(), "tests": results,
        "real_http": {"binding": "127.0.0.1", "checks": checks, "server_stopped": True},
        "source_integrity": repository.catalog()["critical_manifests"],
        "method_version": repository.method["method_version"], "rules_per_strategy": 12,
        "local_agronomic_validation": False, "frontend_implemented": False, "deployed": False,
        "dependencies": {name: importlib.metadata.version(name) for name in (
            "fastapi", "uvicorn", "pydantic", "starlette", "rasterio", "jsonschema", "httpx")},
    })
    print(f"Passed {sum(r['run'] for r in results.values())} tests and {len(checks)} real HTTP checks; data manifests verified, server stopped.")


if __name__ == "__main__":
    main()
