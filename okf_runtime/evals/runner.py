"""Eval orchestration."""

from __future__ import annotations

import json
import shlex
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .adapters import (
    invoke_callable,
    invoke_http,
    invoke_subprocess,
    run_reference_subject,
)
from .baseline import DEFAULT_GATES, evaluate_gates
from .cases import EvalCase
from .config import EvalConfig, load_config
from .isolation import copy_fixture, tree_hash
from .reporters import LangfuseReporter, write_json_result
from .schema import (
    PROTOCOL_VERSION,
    CaseRunResult,
    EvalRunResult,
    RESULT_SCHEMA_VERSION,
    SubjectRequest,
    SubjectResponse,
)
from .scoring import aggregate_scores, score_case


SubjectFn = Callable[[SubjectRequest], SubjectResponse]


class RunnerError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _build_subject(adapter: str, adapter_target: str | None) -> SubjectFn:
    if adapter == "reference":
        return run_reference_subject
    if adapter == "callable":
        if not adapter_target:
            raise RunnerError("Callable adapter requires --target module:callable")
        return lambda request: invoke_callable(adapter_target, request)
    if adapter == "subprocess":
        if not adapter_target:
            raise RunnerError("Subprocess adapter requires --command")
        command = shlex.split(adapter_target)
        return lambda request: invoke_subprocess(command, request, timeout_seconds=float(request.metadata.get("timeout_seconds", 30)))
    if adapter == "http":
        if not adapter_target:
            raise RunnerError("HTTP adapter requires --url")
        url = adapter_target
        return lambda request: invoke_http(url, request, timeout_seconds=float(request.metadata.get("timeout_seconds", 30)))
    raise RunnerError(f"Unknown adapter: {adapter}")


def _invoke_with_timeout(subject: SubjectFn, request: SubjectRequest, timeout_seconds: float) -> SubjectResponse:
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(subject, request)
    try:
        return future.result(timeout=timeout_seconds)
    except FuturesTimeout:
        future.cancel()
        return SubjectResponse(
            protocol_version=PROTOCOL_VERSION,
            case_id=request.case_id,
            status="timeout",
            error="Subject execution timed out",
        )
    except Exception as exc:  # noqa: BLE001 - isolate one subject failure to its case
        message = str(exc) or exc.__class__.__name__
        status = "timeout" if "timed out" in message.lower() or "timeout" in message.lower() else "error"
        return SubjectResponse(
            protocol_version=PROTOCOL_VERSION,
            case_id=request.case_id,
            status=status,  # type: ignore[arg-type]
            error=f"{exc.__class__.__name__}: {message}",
        )
    finally:
        # Do not wait for a timed-out in-process subject.
        pool.shutdown(wait=False, cancel_futures=True)


def _case_request(case: EvalCase, bundle_root: Path) -> SubjectRequest:
    timeout = float(case.metadata.get("timeout_seconds", 30))
    return SubjectRequest(
        protocol_version=PROTOCOL_VERSION,
        case_id=case.id,
        input=dict(case.input),
        context={"bundle_root": str(bundle_root.resolve())},
        metadata={"timeout_seconds": timeout, "suite": case.suite, "plan": case.plan},
    )


def run_cases(
    cases: list[EvalCase],
    *,
    repo_root: Path,
    adapter: str = "reference",
    adapter_target: str | None = None,
    run_name: str | None = None,
    gates: dict[str, float] | None = None,
    work_dir: Path | None = None,
    config: EvalConfig | None = None,
) -> EvalRunResult:
    config = config or load_config()
    subject = _build_subject(adapter, adapter_target)
    run_id = uuid.uuid4().hex
    started_at = _utc_now()
    work_root = work_dir or (repo_root / ".evals-run" / run_id)
    work_root.mkdir(parents=True, exist_ok=True)

    case_results: list[CaseRunResult] = []
    all_scores: list[list] = []

    for case in cases:
        fixture_source = (repo_root / case.fixture).resolve()
        if not fixture_source.exists():
            case_results.append(
                CaseRunResult(
                    case_id=case.id,
                    suite=case.suite,
                    status="error",
                    scores=[],
                    latency_ms=0.0,
                    error_category="fixture_missing",
                )
            )
            continue

        case_dir = work_root / case.id
        copy_fixture(fixture_source, case_dir)
        before_hash = tree_hash(case_dir, extra_ignore=set(case.metadata.get("ignore_paths") or []))

        request = _case_request(case, case_dir)
        timeout = float(case.metadata.get("timeout_seconds", 30))
        start = time.perf_counter()
        response = _invoke_with_timeout(subject, request, timeout)
        latency_ms = (time.perf_counter() - start) * 1000.0

        replay_equivalent: bool | None = None
        if case.expect.get("deterministic_replay"):
            second = _invoke_with_timeout(subject, request, timeout)
            replay_equivalent = response.to_dict() == second.to_dict()

        after_hash = tree_hash(case_dir, extra_ignore=set(case.metadata.get("ignore_paths") or []))
        source_unchanged = before_hash == after_hash

        response_size = len(json.dumps(response.to_dict(), ensure_ascii=True, separators=(",", ":")).encode("utf-8"))
        if len(response.events) > config.max_events:
            response.status = "invalid"
            response.error = "Event count exceeded configured limit"
        elif response_size > config.max_response_bytes:
            response.status = "invalid"
            response.error = "Response size exceeded configured limit"

        scores = score_case(case, response, source_unchanged=source_unchanged, replay_equivalent=replay_equivalent)
        all_scores.append(scores)
        error_category = None
        if response.status != "ok":
            error_category = response.status
        expected_error = any(
            spec.get("path") == "status" and spec.get("value") == "error"
            for spec in (case.expect.get("structured") or [])
        )
        gate_status: str = response.status
        if expected_error and response.status == "error" and all(score.passed for score in scores if score.applicable):
            gate_status = "ok"

        case_results.append(
            CaseRunResult(
                case_id=case.id,
                suite=case.suite,
                status=response.status,
                scores=scores,
                latency_ms=latency_ms,
                error_category=error_category,
                gate_status=gate_status,  # type: ignore[arg-type]
                subject_response=response.to_dict(),
                evidence={"source_hash_before": before_hash, "source_hash_after": after_hash},
            )
        )

    aggregates = aggregate_scores(all_scores)
    gate_config = {**DEFAULT_GATES, **(gates or {})}
    gate_result = evaluate_gates(aggregates, [case.to_dict() for case in case_results], gate_config)
    finished_at = _utc_now()

    result = EvalRunResult(
        result_schema_version=RESULT_SCHEMA_VERSION,
        run_id=run_id,
        run_name=run_name or f"okf-evals-{adapter}",
        adapter=adapter,
        started_at=started_at,
        finished_at=finished_at,
        cases=case_results,
        aggregates=aggregates,
        gates={"passed": gate_result["passed"], "checks": gate_result["checks"], "config": gate_config},
        publication={"enabled": config.publish_langfuse, "status": "pending"},
        metadata={
            "python_version": sys.version.split()[0],
            "case_count": len(cases),
            "protocol_version": PROTOCOL_VERSION,
        },
    )
    return result


def run_and_write(
    cases: list[EvalCase],
    *,
    repo_root: Path,
    output_path: Path,
    adapter: str = "reference",
    adapter_target: str | None = None,
    run_name: str | None = None,
    gates: dict[str, float] | None = None,
    config: EvalConfig | None = None,
) -> EvalRunResult:
    config = config or load_config()
    result = run_cases(
        cases,
        repo_root=repo_root,
        adapter=adapter,
        adapter_target=adapter_target,
        run_name=run_name,
        gates=gates,
        config=config,
    )
    write_json_result(result, output_path)
    if config.publish_langfuse:
        try:
            reporter = LangfuseReporter.from_config(config)
            result.publication = reporter.publish(result)
        except ValueError as exc:
            result.publication = {"enabled": True, "status": "failed", "error": str(exc)}
            write_json_result(result, output_path)
    else:
        result.publication = {"enabled": False, "status": "skipped"}
    return result
