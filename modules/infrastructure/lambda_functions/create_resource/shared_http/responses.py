import json
from typing import Any, Dict, Optional

JsonDict = Dict[str, Any]

def _headers(correlation_id: Optional[str], content_type: str) -> Dict[str, str]:
    h = {"Content-Type": content_type}
    if correlation_id:
        h["X-Correlation-Id"] = correlation_id
    return h


def ok(status_code: int, body: Any, correlation_id: Optional[str] = None, content_type: str = "application/fhir+json") -> JsonDict:
    return {
        "statusCode": status_code,
        "headers": _headers(correlation_id, content_type),
        "body": json.dumps(body, ensure_ascii=False),
    }


def err(status_code: int, code: str, message: str, *, details: Any = None, correlation_id: Optional[str] = None) -> JsonDict:
    payload: JsonDict = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details
    if correlation_id:
        payload["correlationId"] = correlation_id

    return {
        "statusCode": status_code,
        "headers": _headers(correlation_id, "application/json"),
        "body": json.dumps(payload, ensure_ascii=False),
    }
