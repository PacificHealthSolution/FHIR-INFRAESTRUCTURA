import os
import logging

from clients.healthlake import HealthLakeFHIRPutClient
from shared_http.responses import ok, err

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DATASTORE_ID = os.environ.get("DATASTORE_ID")
REGION = os.environ.get("REGION")

HL = HealthLakeFHIRPutClient(datastore_id=DATASTORE_ID, region_name=REGION)


def handler(event, context):
    correlation_id = (event or {}).get("correlationId")

    if not event or "fhir" not in event:
        return err(400, "BadRequest", "Missing required key: fhir", correlation_id=correlation_id)

    fhir = event["fhir"]
    if not isinstance(fhir, dict):
        return err(400, "BadRequest", "Key 'fhir' must be an object", correlation_id=correlation_id)

    resource_type = event.get("resourceType") or fhir.get("resourceType")
    resource_id = event.get("id") or fhir.get("id")

    if not resource_type or not resource_id:
        return err(422, "UnprocessableEntity", "PUT requires resourceType and id", correlation_id=correlation_id)

    fhir["resourceType"] = resource_type
    fhir["id"] = resource_id

    try:
        status, payload = HL.put(fhir, resource_type, resource_id)
        if status >= 400:
            return err(status, "HealthLakeError", "HealthLake returned an error", details=payload, correlation_id=correlation_id)
        return ok(status or 200, payload, correlation_id=correlation_id)

    except ValueError as e:
        return err(422, "UnprocessableEntity", str(e), correlation_id=correlation_id)

    except Exception as e:
        logger.exception("Unhandled error in PUT handler")
        return err(500, "InternalError", "Unhandled error in PUT handler", details=str(e), correlation_id=correlation_id)
