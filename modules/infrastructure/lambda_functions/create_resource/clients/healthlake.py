import boto3
import json
import logging

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.httpsession import URLLib3Session

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class HealthLakeFHIRPostClient:
    def __init__(self, datastore_id: str, region_name: str):
        self.datastore_id = datastore_id
        self.region_name = region_name

        session = boto3.Session(region_name=region_name)
        self.credentials = session.get_credentials()

        hl = boto3.client("healthlake", region_name=region_name)
        info = hl.describe_fhir_datastore(DatastoreId=datastore_id)
        self.fhir_endpoint = info["DatastoreProperties"]["DatastoreEndpoint"].rstrip("/")

        self.http = URLLib3Session()

    def _request(self, path: str, data: dict | None = None) -> tuple[int, dict]:
        url = f"{self.fhir_endpoint}/{path.lstrip('/')}"
        headers = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
        }

        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None

        req = AWSRequest(method="POST", url=url, data=body, headers=headers)
        SigV4Auth(self.credentials, "healthlake", self.region_name).add_auth(req)

        prepared = req.prepare()
        resp = self.http.send(prepared)

        status = resp.status_code
        text = resp.content.decode("utf-8", errors="replace") if resp.content else ""

        payload = {}
        if text:
            try:
                payload = json.loads(text)
            except Exception:
                payload = {"raw": text}

        if status >= 400:
            logger.error(f"HealthLake FHIR error {status}: {text}")

        return status, payload

    def post(self, fhir: dict) -> tuple[int, dict]:
        rt = (fhir.get("resourceType") or "").strip()
        if not rt:
            raise ValueError("FHIR payload missing resourceType")

        if rt == "Bundle":
            return self._request("/", fhir)

        return self._request(f"/{rt}", fhir)
