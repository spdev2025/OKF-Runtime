"""Optional Langfuse publication layer."""

from __future__ import annotations

from typing import Any, Protocol

from ..config import EvalConfig
from ..redaction import redact_run_result
from ..schema import EvalRunResult


class LangfuseClientProtocol(Protocol):
    def trace(self, **kwargs: Any) -> Any: ...

    def score(self, **kwargs: Any) -> Any: ...

    def flush(self) -> None: ...


class LangfuseReporter:
    def __init__(self, client: LangfuseClientProtocol | None, config: EvalConfig) -> None:
        self.client = client
        self.config = config

    @classmethod
    def from_config(cls, config: EvalConfig) -> LangfuseReporter:
        if not config.publish_langfuse:
            return cls(None, config)
        if not config.langfuse_public_key or not config.langfuse_secret_key:
            raise ValueError("Langfuse publish requested but LANGFUSE_PUBLIC_KEY/SECRET_KEY are missing")
        try:
            from langfuse import Langfuse
        except ImportError as exc:
            raise ValueError("Langfuse publish requested but langfuse package is not installed") from exc
        client = Langfuse(
            public_key=config.langfuse_public_key,
            secret_key=config.langfuse_secret_key,
            host=config.langfuse_host,
        )
        return cls(client, config)

    def publish(self, result: EvalRunResult) -> dict[str, Any]:
        if self.client is None:
            return {"enabled": False, "status": "skipped"}
        sanitized = redact_run_result(result.to_dict())
        run_name = result.run_name
        try:
            for case in sanitized.get("cases", []):
                trace = self.client.trace(
                    name=f"okf-eval:{case['case_id']}",
                    metadata={
                        "run_id": result.run_id,
                        "run_name": run_name,
                        "adapter": result.adapter,
                        "suite": case.get("suite"),
                    },
                    input={"case_id": case["case_id"]},
                    output=case.get("subject_response"),
                )
                trace_id = getattr(trace, "id", None) or getattr(trace, "trace_id", None)
                for score in case.get("scores", []):
                    if not score.get("applicable"):
                        continue
                    self.client.score(
                        trace_id=trace_id,
                        name=str(score["name"]),
                        value=float(score["value"]) if score.get("data_type") == "numeric" else score["value"],
                        comment=str(score.get("comment") or ""),
                    )
            self.client.flush()
            return {"enabled": True, "status": "published", "run_name": run_name}
        except Exception as exc:  # noqa: BLE001 - publication must not crash runner
            return {"enabled": True, "status": "failed", "error": str(exc)}
