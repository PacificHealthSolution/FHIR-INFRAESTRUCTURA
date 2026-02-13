from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

JsonDict = Dict[str, Any]


class FhirMapper:
    @staticmethod
    def _as_dict(data: Any) -> JsonDict:
        if data is None:
            return {}
        if isinstance(data, dict):
            return data
        if isinstance(data, BaseModel):
            return data.model_dump(exclude_none=True)
        raise TypeError(f"Unsupported input type for mapping: {type(data)}")

    @staticmethod
    def _drop_nones(obj: Any) -> Any:
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                vv = FhirMapper._drop_nones(v)
                if vv is not None:
                    out[k] = vv
            return out
        if isinstance(obj, list):
            out_list = []
            for v in obj:
                vv = FhirMapper._drop_nones(v)
                if vv is not None:
                    out_list.append(vv)
            return out_list
        return obj

    @staticmethod
    def _require(data: Any, keys: List[str], label: str = "") -> None:
        d = FhirMapper._as_dict(data)
        missing = [k for k in keys if (k not in d or d[k] in (None, ""))]
        if missing:
            prefix = f"{label}: " if label else ""
            raise ValueError(f"{prefix}Missing required fields: {missing}")

    def map_organization(self, organization_data: Any) -> JsonDict:
        return self._convert_to_fhir_organization(organization_data)

    def map_location(self, location_data: Any) -> JsonDict:
        return self._convert_to_fhir_location(location_data)

    def map_practitioner(self, profesional_data: Any) -> JsonDict:
        return self._convert_to_fhir_profesional(profesional_data)

    def map_patient(self, patient_data: Any) -> JsonDict:
        return self._convert_to_fhir_patient(patient_data)

    def map_coverage(self, coverage_data: Any) -> JsonDict:
        return self._convert_to_fhir_coverage(coverage_data)


    def map_bundle_transaction(
        self,
        *,
        organization: Optional[Any] = None,
        location: Optional[Any] = None,
        practitioner: Optional[Any] = None,
        patient: Optional[Any] = None,
        coverage: Optional[Any] = None,
        method: str = "POST",
        group_id: Optional[str] = None,
    ) -> JsonDict:
        method = method.upper()
        if method not in ("POST", "PUT"):
            raise ValueError("method must be POST or PUT")

        if method == "PUT" and not group_id:
            raise ValueError("group_id is required for PUT bundle transaction")

        entry: List[JsonDict] = []

        def _add(resource: JsonDict):
            rt = resource.get("resourceType")
            if not rt:
                raise ValueError("Mapped resource missing resourceType")

            if method == "PUT":
                resource["id"] = group_id
                url = f"{rt}/{group_id}"
            else:
                url = rt

            entry.append(
                {
                    "resource": self._drop_nones(resource),
                    "request": {"method": method, "url": url},
                }
            )

        if organization is not None:
            _add(self.map_organization(organization))

        if location is not None:
            _add(self.map_location(location))

        if practitioner is not None:
            _add(self.map_practitioner(practitioner))

        if patient is not None:
            _add(self.map_patient(patient))

        if coverage is not None:
            _add(self.map_coverage(coverage))

        bundle = {"resourceType": "Bundle", "type": "transaction", "entry": entry}
        return self._drop_nones(bundle)


    def _convert_to_fhir_coverage(self, coverage_data: Any) -> JsonDict:
        cov = self._as_dict(coverage_data)

        self._require(
            cov,
            ["beneficiary_id", "payor_id", "start", "subscriber_id", "relationship_code", "value", "name"],
            label="Coverage",
        )

        coverage: JsonDict = {
            "resourceType": "Coverage",
            "status": "active",
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": cov.get("type_code") or "EHCPOL",
                        "display": cov.get("type_display") or "Extended healthcare",
                    }
                ]
            },
            "beneficiary": {"reference": f"Patient/{cov['beneficiary_id']}"},
            "payor": [{"reference": f"Organization/{cov['payor_id']}"}],
            "period": {"start": cov["start"], "end": cov.get("end")},
            "class": [
                {
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/coverage-class",
                                "code": cov.get("class_code") or "plan",
                                "display": cov.get("class_display") or "Plan",
                            }
                        ]
                    },
                    "value": cov["value"],
                    "name": cov["name"],
                }
            ],
            "relationship": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
                        "code": cov.get("relationship_code") or "self",
                    }
                ]
            },
            "subscriberId": cov["subscriber_id"],
        }

        if cov.get("type_text"):
            coverage["type"]["text"] = cov["type_text"]

        if cov.get("beneficiary_display"):
            coverage["beneficiary"]["display"] = cov["beneficiary_display"]

        if cov.get("payor_display"):
            coverage["payor"][0]["display"] = cov["payor_display"]

        if cov.get("class_text"):
            coverage["class"][0]["type"]["text"] = cov["class_text"]

        return self._drop_nones(coverage)



    def _convert_to_fhir_organization(self, organization_data: Any) -> JsonDict:
        org = self._as_dict(organization_data)

        self._require(
            org,
            [
                "active",
                "name",
                "identifier_value",
                "identifier_type",
                "provider_identifier",
                "provider_class",
                "phone",
                "address_line",
                "city",
                "country",
            ],
            label="Organization",
        )

        organization = {
            "resourceType": "Organization",
            "active": org["active"],
            "name": org["name"],
            "identifier": [
                {
                    "use": "official",
                    "system": "https://vulcano.ihcecol.gov.co/ids/organization",
                    "value": org["identifier_value"],
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.fhir.guide/co/CodeSystem/ColombianOrganizationIdentifiers",
                                "code": org["identifier_type"],
                                "display": org["identifier_type"],
                            },
                            {
                                "system": "https://fhir.minsalud.gov.co/rda/CodeSystem/ColombianOrganizationIdentifiers",
                                "code": org["provider_identifier"],
                                "display": org["provider_identifier"],
                            },
                        ]
                    },
                }
            ],
            "type": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                            "code": org["provider_class"],
                            "display": org["provider_class"],
                        }
                    ],
                    "text": org["provider_class"],
                }
            ],
            "telecom": [{"system": "phone", "value": org["phone"]}],
            "address": [
                {
                    "use": "work",
                    "type": "both",
                    "line": [org["address_line"]],
                    "city": org["city"],
                    "country": org["country"],
                }
            ],
        }
        return self._drop_nones(organization)

    def _convert_to_fhir_location(self, location_data: Any) -> JsonDict:
        loc = self._as_dict(location_data)

        identifier_value = loc.get("identifier_value")
        identifier_system = loc.get("identifier_system") or "urn:demo:location"

        location: JsonDict = {"resourceType": "Location"}

        if identifier_value:
            location["identifier"] = [{"use": "official", "system": identifier_system, "value": str(identifier_value)}]

        for k in ["status", "name", "alias", "description", "mode"]:
            if loc.get(k) is not None:
                location[k] = loc[k]

        if loc.get("type_codings") is not None:
            location["type"] = [
                {
                    "coding": [
                        {kk: vv for kk, vv in c.items() if vv is not None}
                        for c in (loc.get("type_codings") or [])
                    ]
                }
            ]

        address_in = loc.get("address") or {}
        line = address_in.get("line") or ([loc.get("address_line")] if loc.get("address_line") else None)

        address: JsonDict = {}
        for key in ["use", "type", "text"]:
            if address_in.get(key) is not None:
                address[key] = address_in[key]

        if line:
            address["line"] = line if isinstance(line, list) else [str(line)]

        if (address_in.get("city") or loc.get("city")) is not None:
            address["city"] = address_in.get("city") or loc.get("city")
        if (address_in.get("district") or loc.get("district")) is not None:
            address["district"] = address_in.get("district") or loc.get("district")
        if (address_in.get("state") or loc.get("state")) is not None:
            address["state"] = address_in.get("state") or loc.get("state")
        if (address_in.get("postalCode") or loc.get("postal_code")) is not None:
            address["postalCode"] = address_in.get("postalCode") or loc.get("postal_code")
        if (address_in.get("country") or loc.get("country")) is not None:
            address["country"] = address_in.get("country") or loc.get("country")

        if address:
            location["address"] = address

        pos = loc.get("position") or {}
        if pos.get("longitude") is not None and pos.get("latitude") is not None:
            location["position"] = {"longitude": float(pos["longitude"]), "latitude": float(pos["latitude"])}
            if pos.get("altitude") is not None:
                location["position"]["altitude"] = float(pos["altitude"])

        if loc.get("managing_organization_id"):
            location["managingOrganization"] = {"reference": f"Organization/{loc['managing_organization_id']}"}

        if loc.get("part_of_location_id"):
            location["partOf"] = {"reference": f"Location/{loc['part_of_location_id']}"}

        return self._drop_nones(location)

    def _convert_to_fhir_profesional(self, profesional_data: Any) -> JsonDict:
        pr = self._as_dict(profesional_data)

        self._require(
            pr,
            ["nombres", "apellidos", "documento", "rethus", "profesion", "especialidad", "datos_academicos"],
            label="Practitioner",
        )

        documento = pr.get("documento") or {}
        self._require(documento, ["tipo", "numero"], label="Practitioner.documento")

        datos_academicos = pr.get("datos_academicos") or {}
        self._require(datos_academicos, ["universidad"], label="Practitioner.datos_academicos")

        ext_items = [{"url": "universidad", "valueString": datos_academicos["universidad"]}]

        titulo = datos_academicos.get("titulo")
        if isinstance(titulo, str):
            titulo = titulo.strip()
        if titulo:
            ext_items.append({"url": "titulo", "valueString": titulo})

        fhir_profesional: JsonDict = {
            "resourceType": "Practitioner",
            "name": [{"given": [pr["nombres"]], "family": pr["apellidos"]}],
            "identifier": [
                {
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MD"}]},
                    "value": documento["numero"],
                    "system": f"http://hospital.smarthealth.example/{documento['tipo']}",
                },
                {
                    "type": {"coding": [{"system": "http://hospital.smarthealth.example/rethus", "code": "RETHUS"}]},
                    "value": pr["rethus"],
                },
            ],
            "qualification": [
                {
                    "code": {
                        "text": pr["profesion"],
                        "coding": [{"system": "http://hospital.smarthealth.example/profesion", "code": pr["profesion"]}],
                    }
                },
                {
                    "code": {
                        "text": pr["especialidad"],
                        "coding": [{"system": "http://hospital.smarthealth.example/especialidad", "code": pr["especialidad"]}],
                    }
                },
            ],
            "extension": [
                {
                    "url": "http://hospital.smarthealth.example/datos-academicos",
                    "extension": ext_items,
                }
            ],
        }

        anio = datos_academicos.get("anio_graduacion")
        if anio is not None:
            fhir_profesional["extension"][0]["extension"].append({"url": "anio_graduacion", "valueInteger": int(anio)})

        contacto = pr.get("contacto") or {}
        telecom = []
        if contacto.get("telefono"):
            telecom.append({"system": "phone", "value": contacto["telefono"]})
        if contacto.get("email"):
            telecom.append({"system": "email", "value": str(contacto["email"])})
        if telecom:
            fhir_profesional["telecom"] = telecom

        direccion = pr.get("direccion") or {}
        if direccion:
            fhir_profesional["address"] = [
                {
                    "line": [direccion.get("linea")],
                    "city": direccion.get("ciudad"),
                    "state": direccion.get("departamento"),
                    "country": direccion.get("pais"),
                }
            ]

        especialidades_extra = pr.get("especialidades") or []
        if especialidades_extra:
            fhir_profesional["qualification"].extend(
                [
                    {
                        "code": {
                            "text": esp.get("nombre"),
                            "coding": (
                                [{"system": "http://terminology.hl7.org/CodeSystem/v2-2.7", "code": esp.get("codigo")}]
                                if esp.get("codigo")
                                else []
                            ),
                        }
                    }
                    for esp in especialidades_extra
                ]
            )

        if pr.get("institucion"):
            fhir_profesional["extension"].append(
                {"url": "http://hospital.smarthealth.example/institucion", "valueString": pr["institucion"]}
            )

        return self._drop_nones(fhir_profesional)

    def _convert_to_fhir_patient(self, patient_data: Any) -> JsonDict:
        pt = self._as_dict(patient_data)

        if "primer_nombre" not in pt and pt.get("nombres"):
            parts = str(pt["nombres"]).strip().split()
            pt["primer_nombre"] = parts[0] if parts else ""
            pt["segundo_nombre"] = " ".join(parts[1:]) if len(parts) > 1 else None

        if "primer_apellido" not in pt and pt.get("apellidos"):
            parts = str(pt["apellidos"]).strip().split()
            pt["primer_apellido"] = parts[0] if parts else ""
            pt["segundo_apellido"] = " ".join(parts[1:]) if len(parts) > 1 else None

        if "sexo_biologico" not in pt and pt.get("genero"):
            pt["sexo_biologico"] = pt["genero"]

        required = [
            "primer_nombre",
            "segundo_nombre",
            "primer_apellido",
            "segundo_apellido",
            "documento",
            "fecha_nacimiento",
            "nacionalidad",
            "sexo_biologico",
            "identidad_genero",
            "etnia",
            "comunidad_etnica",
            "categoria_discapacidad",
            "residencia",
        ]
        missing = [k for k in required if (k not in pt or pt[k] in (None, ""))]
        if missing:
            raise ValueError(f"Missing required fields (Res.1888): {missing}")

        nacionalidad = pt.get("nacionalidad") or {}
        residencia = pt.get("residencia") or {}
        documento = pt.get("documento") or {}

        for k in ["codigo_pais", "pais"]:
            if k not in nacionalidad or nacionalidad[k] in (None, ""):
                missing.append(f"nacionalidad.{k}")
        for k in ["codigo_pais", "pais", "codigo_municipio", "municipio", "zona_territorial"]:
            if k not in residencia or residencia[k] in (None, ""):
                missing.append(f"residencia.{k}")
        for k in ["tipo", "numero"]:
            if k not in documento or documento[k] in (None, ""):
                missing.append(f"documento.{k}")

        if missing:
            raise ValueError(f"Missing required fields (Res.1888): {missing}")

        given = [pt["primer_nombre"]]
        if pt.get("segundo_nombre"):
            given.append(pt["segundo_nombre"])

        family_parts = [pt["primer_apellido"]]
        if pt.get("segundo_apellido"):
            family_parts.append(pt["segundo_apellido"])
        family = " ".join(family_parts)

        fhir_patient: JsonDict = {
            "resourceType": "Patient",
            "name": [{"given": given, "family": family}],
            "birthDate": pt["fecha_nacimiento"],
            "gender": pt.get("sexo_biologico") or "unknown",
            "identifier": [
                {
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]},
                    "value": documento["numero"],
                    "system": f"http://hospital.smarthealth.example/{documento['tipo']}",
                }
            ],
            "extension": [],
        }

        fhir_patient["extension"].extend(
            [
                {"url": "http://hospital.smarthealth.example/identidad-genero", "valueString": pt["identidad_genero"]},
                {"url": "http://hospital.smarthealth.example/etnia", "valueString": pt["etnia"]},
                {"url": "http://hospital.smarthealth.example/comunidad-etnica", "valueString": pt["comunidad_etnica"]},
                {"url": "http://hospital.smarthealth.example/categoria-discapacidad", "valueString": pt["categoria_discapacidad"]},
                {
                    "url": "http://hospital.smarthealth.example/nacionalidad",
                    "extension": [
                        {"url": "codigo_pais", "valueString": nacionalidad["codigo_pais"]},
                        {"url": "pais", "valueString": nacionalidad["pais"]},
                    ],
                },
            ]
        )

        direccion = pt.get("direccion") or {}
        address = {
            "country": residencia.get("codigo_pais"),
            "extension": [
                {"url": "http://hospital.smarthealth.example/pais-residencia-nombre", "valueString": residencia.get("pais")},
                {"url": "http://hospital.smarthealth.example/municipio-codigo", "valueString": residencia.get("codigo_municipio")},
                {"url": "http://hospital.smarthealth.example/municipio-nombre", "valueString": residencia.get("municipio")},
                {"url": "http://hospital.smarthealth.example/zona-territorial", "valueString": residencia.get("zona_territorial")},
            ],
        }
        if direccion.get("linea"):
            address["line"] = [direccion["linea"]]
        if direccion.get("departamento"):
            address["state"] = direccion["departamento"]
        fhir_patient["address"] = [address]

        contacto = pt.get("contacto") or {}
        telecom = []
        if contacto.get("telefono"):
            telecom.append({"system": "phone", "value": contacto["telefono"]})
        if contacto.get("email"):
            telecom.append({"system": "email", "value": str(contacto["email"])})
        if telecom:
            fhir_patient["telecom"] = telecom

        if pt.get("informacion_discapacidad"):
            info = pt["informacion_discapacidad"]
            fhir_patient["extension"].append(
                {
                    "url": "http://hospital.smarthealth.example/disability-info",
                    "extension": [
                        {"url": "type", "valueString": info["tipo_discapacidad"]},
                        {"url": "description", "valueString": info["descripcion"]},
                        {"url": "percentage", "valueInteger": info["porcentaje_discapacidad"]},
                        {"url": "certification_date", "valueDate": info["fecha_certificacion"]},
                        {"url": "entity", "valueString": info["entidad_certificadora"]},
                        {"url": "wheelchair_required", "valueBoolean": info["requiere_silla_ruedas"]},
                        {"url": "personal_assistance_required", "valueBoolean": info["requiere_asistencia_personal"]},
                    ],
                }
            )

        if pt.get("necesidades_especiales"):
            ne = pt["necesidades_especiales"]
            fhir_patient["extension"].append(
                {
                    "url": "http://hospital.smarthealth.example/special-needs",
                    "extension": [
                        {"url": "physical_accessibility", "valueBoolean": ne["accesibilidad_fisica"]},
                        {"url": "sign_language_communication", "valueBoolean": ne["comunicacion_lenguaje_señas"]},
                        {"url": "braille_material", "valueBoolean": ne["material_braille"]},
                        {"url": "interpreter_required", "valueBoolean": ne["interprete_requerido"]},
                        {"url": "additional_time_consultation", "valueBoolean": ne["tiempo_adicional_consulta"]},
                        {"url": "specialized_transport", "valueBoolean": ne["transporte_especializado"]},
                    ],
                }
            )

        if pt.get("cuidador_principal"):
            cp = pt["cuidador_principal"]
            fhir_patient.setdefault("contact", [])
            fhir_patient["contact"].append(
                {
                    "relationship": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                                    "code": "C",
                                    "display": cp["relacion"],
                                }
                            ]
                        }
                    ],
                    "name": {"given": [cp["nombres"]], "family": cp["apellidos"]},
                    "telecom": [{"system": "phone", "value": cp["telefono"]}],
                }
            )

        if not fhir_patient["extension"]:
            del fhir_patient["extension"]

        return self._drop_nones(fhir_patient)
