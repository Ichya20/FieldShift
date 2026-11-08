"""Run the stage-2 reference checks and regenerate review artifacts."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import json
import platform
import re
import sys
import unittest

from build_rotation_demo import ROOT, build_report, load, write_report


def reject_nonfinite(value):
    raise ValueError(f"Non-finite JSON value: {value}")


def main():
    sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests/method"), pattern="test_*.py")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    print(stream.getvalue(), end="")
    if not result.wasSuccessful():
        raise SystemExit(1)

    report = build_report()
    write_report(report)
    spec = load(ROOT / "specs/rotation-method-v1.json")
    source_ids = {s["id"] for s in load(ROOT / "data/prepared/agronomy/source-evidence.json")["sources"]}
    source_ids.update(spec["additional_source_refs"])
    for rule in spec["rules"]:
        if not set(rule["source_refs"]) <= source_ids:
            raise ValueError(f"Unresolved rule sources: {rule['id']}")
    for ref in spec["additional_source_refs"].values():
        if "path" in ref and not (ROOT / ref["path"]).is_file():
            raise ValueError(f"Missing source reference: {ref['path']}")

    verification_path = ROOT / "outputs/rotation-method-verification.json"
    checked_links = []
    for relative in ("docs/rotation-method.md", "docs/roadmap.md", "outputs/rotation-method-demo.md"):
        document = ROOT / relative
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            local = (document.parent / target.split("#", 1)[0]).resolve()
            if local != verification_path and not local.is_file():
                raise ValueError(f"Broken local link in {relative}: {target}")
            checked_links.append({"document": relative, "target": target})

    paths = [ROOT / "specs/rotation-method-v1.json", ROOT / "specs/fixtures/rotation-demo.json",
             ROOT / "outputs/rotation-method-demo.json"]
    for path in paths:
        json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_nonfinite)

    verification = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "method_version": spec["method_version"],
        "python_version": platform.python_version(),
        "command": "py -3.11 scripts/method/verify_rotation_method.py",
        "status": "passed_reference_checks_not_local_agronomic_validation",
        "tests": {"run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                  "skipped": len(result.skipped)},
        "demo_checks": report["checks_passed"],
        "rule_count": len(spec["rules"]), "all_rule_source_ids_resolve": True,
        "local_markdown_links_checked": checked_links,
        "source_integrity": report["source_integrity"],
        "local_agronomic_validation": False,
        "application_implemented": False,
    }
    verification_path.write_text(json.dumps(verification, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                                 encoding="utf-8")
    print(f"Verified {result.testsRun} tests, {len(spec['rules'])} rules, "
          f"{report['source_integrity']['sha256_files_verified']} prepared-source hashes.")


if __name__ == "__main__":
    main()
