import json
import os
import boto3
from pydantic import ValidationError

from fhir_mapper import FhirMapper
from models import PayerDataIn, Location, ProfesionalData, PatientData, CoverageDataIn

lambda_client = boto3.client("lambda")

POST_FN = os.environ["POST_LAMBDA_NAME"]
PUT_FN = os.environ["PUT_LAMBDA_NAME"]


def _api_resp(status, payload, correlation_id=None, content_type="application/json"):
    headers = {"Content-Type": content_type}
    if correlation_id:
        headers["X-Correlation-Id"] = correlation_id
    return {"statusCode": status, "headers": headers, "body": json.dumps(payload, ensure_ascii=False)}


def _get_method(event):
    return (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or ""
    ).upper()


def _get_path_params(event):
    return event.get("pathParameters") or {}


def _get_correlation_id(event):
    h = event.get("headers") or {}
    return h.get("x-correlation-id") or h.get("X-Correlation-Id") or event.get("requestContext", {}).get("requestId")


def _parse_body(event):
    body = event.get("body")
    if body is None:
        return {}
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode("utf-8")
    return json.loads(body) if isinstance(body, str) else body


def _invoke(fn_name, payload: dict):
    resp = lambda_client.invoke(
        FunctionName=fn_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode("utf-8"),
    )
    raw = resp["Payload"].read().decode("utf-8")
    return json.loads(raw) if raw else {}


def handler(event, context):
    correlation_id = _get_correlation_id(event)

    try:
        method = _get_method(event)
        body = _parse_body(event)
        path_params = _get_path_params(event)
    except Exception as e:
        return _api_resp(400, {"code": "BadRequest", "message": "Invalid request", "details": str(e)}, correlation_id)

    mapper = FhirMapper()

    if method == "POST":
        try:
            org = PayerDataIn.model_validate(body["organization"]).model_dump(exclude_none=True)
            loc = Location.model_validate(body["location"]).model_dump(exclude_none=True)
            prac = ProfesionalData.model_validate(body["practitioner"]).model_dump(exclude_none=True)
            pat = PatientData.model_validate(body["patient"]).model_dump(exclude_none=True)
            cov = CoverageDataIn.model_validate(body["coverage"]).model_dump(exclude_none=True) 
        except KeyError as e:
            return _api_resp(400, {"code": "BadRequest", "message": f"Missing top-level key: {str(e)}"}, correlation_id)
        except ValidationError as e:
            return _api_resp(422, {"code": "ValidationError", "message": "Invalid payload", "details": e.errors()}, correlation_id)

        try:
            fhir_payload = mapper.map_bundle_transaction(
                organization=org,
                location=loc,
                practitioner=prac,
                patient=pat,
                coverage=cov
            )
        except Exception as e:
            return _api_resp(422, {"code": "MappingError", "message": "Failed to map to FHIR", "details": str(e)}, correlation_id)

        downstream = _invoke(POST_FN, {"correlationId": correlation_id, "fhir": fhir_payload})
        return downstream

    if method == "PUT":
        resource_id = path_params.get("id") or body.get("id")
        if not resource_id:
            return _api_resp(422, {"code": "UnprocessableEntity", "message": "Missing resource id for PUT"}, correlation_id)

        resource_type = body.get("resourceType")
        fhir = body.get("fhir") or body.get("resource")

        if fhir is None:
            if isinstance(body, dict) and ("patient" in body or "organization" in body or "location" in body or "practitioner" in body):
                if "patient" in body:
                    resource_type = resource_type or "Patient"
                    fhir = mapper.map_patient(PatientData.model_validate(body["patient"]).model_dump(exclude_none=True))
                elif "organization" in body:
                    resource_type = resource_type or "Organization"
                    fhir = mapper.map_organization(PayerDataIn.model_validate(body["organization"]).model_dump(exclude_none=True))
                elif "location" in body:
                    resource_type = resource_type or "Location"
                    fhir = mapper.map_location(Location.model_validate(body["location"]).model_dump(exclude_none=True))
                elif "practitioner" in body:
                    resource_type = resource_type or "Practitioner"
                    fhir = mapper.map_practitioner(ProfesionalData.model_validate(body["practitioner"]).model_dump(exclude_none=True))
                elif "coverage" in body:
                    resource_type = resource_type or "Coverage"
                    fhir = mapper.map_coverage(CoverageDataIn.model_validate(body["coverage"]).model_dump(exclude_none=True))
            else:
                fhir = dict(body) if isinstance(body, dict) else None

        if not isinstance(fhir, dict):
            return _api_resp(400, {"code": "BadRequest", "message": "PUT requires a JSON object for the resource"}, correlation_id)

        resource_type = resource_type or fhir.get("resourceType")
        if not resource_type:
            return _api_resp(422, {"code": "UnprocessableEntity", "message": "Missing resourceType for PUT"}, correlation_id)

        fhir["resourceType"] = resource_type
        fhir["id"] = resource_id

        downstream = _invoke(
            PUT_FN,
            {
                "correlationId": correlation_id,
                "resourceType": resource_type,
                "id": resource_id,
                "fhir": fhir,
            },
        )
        return downstream

    return _api_resp(405, {"code": "MethodNotAllowed", "message": f"Unsupported method: {method}"}, correlation_id)
