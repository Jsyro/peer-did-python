from enum import Enum
from typing import List, Optional, Dict, Union, Tuple

from peerdid.core.jwk_okp import get_verification_method_type
from peerdid.errors import MalformedPeerDIDDocError
from peerdid.types import (
    VerificationMethodType,
    VerificationMethodTypeAuthentication,
    VerificationMethodTypeAgreement,
    VerificationMaterial,
    VerificationMaterialFormat,
    VerificationMaterialAuthentication,
    VerificationMaterialAgreement,
)


class VerificationMethodField(Enum):
    BASE58 = "publicKeyBase58"
    MULTIBASE = "publicKeyMultibase"
    JWK = "publicKeyJwk"


SERVICE_ID = "id"
SERVICE_TYPE = "type"
SERVICE_ENDPOINT = "serviceEndpoint"
SERVICE_DIDCOMM_MESSAGING = "DIDCommMessaging"
SERVICE_ROUTING_KEYS = "routingKeys"
SERVICE_ACCEPT = "accept"


class VerificationMethod:
    def __init__(self, id: str, controller: str, ver_material: VerificationMaterial):
        self.id = id
        self.controller = controller
        self.ver_material = ver_material

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.ver_material.type.value,
            "controller": self.controller,
            self.public_key_field.value: self.ver_material.value,
        }

    @property
    def public_key_field(self):
        if self.ver_material.format == VerificationMaterialFormat.BASE58:
            return VerificationMethodField.BASE58
        elif self.ver_material.format == VerificationMaterialFormat.MULTIBASE:
            return VerificationMethodField.MULTIBASE
        elif self.ver_material.format == VerificationMaterialFormat.JWK:
            return VerificationMethodField.JWK
        else:
            raise ValueError(
                "Unsupported verification material format "
                + str(self.ver_material.format)
            )

    @classmethod
    def _get_public_key_format(
        cls, ver_method_type: VerificationMethodType
    ) -> Tuple[VerificationMaterialFormat, VerificationMethodField]:
        if (
            ver_method_type
            == VerificationMethodTypeAgreement.X25519_KEY_AGREEMENT_KEY_2019
        ):
            return VerificationMaterialFormat.BASE58, VerificationMethodField.BASE58
        if (
            ver_method_type
            == VerificationMethodTypeAgreement.X25519_KEY_AGREEMENT_KEY_2020
        ):
            return (
                VerificationMaterialFormat.MULTIBASE,
                VerificationMethodField.MULTIBASE,
            )
        if ver_method_type == VerificationMethodTypeAgreement.JSON_WEB_KEY_2020:
            return VerificationMaterialFormat.JWK, VerificationMethodField.JWK
        if (
            ver_method_type
            == VerificationMethodTypeAuthentication.ED25519_VERIFICATION_KEY_2018
        ):
            return VerificationMaterialFormat.BASE58, VerificationMethodField.BASE58
        if (
            ver_method_type
            == VerificationMethodTypeAuthentication.ED25519_VERIFICATION_KEY_2020
        ):
            return (
                VerificationMaterialFormat.MULTIBASE,
                VerificationMethodField.MULTIBASE,
            )
        if ver_method_type == VerificationMethodTypeAuthentication.JSON_WEB_KEY_2020:
            return VerificationMaterialFormat.JWK, VerificationMethodField.JWK
        raise ValueError("Unsupported verification method type " + str(ver_method_type))

    @classmethod
    def _get_ver_method_type(cls, value: dict) -> VerificationMethodType:
        ver_method_type_str = value["type"]
        if (
            ver_method_type_str
            == VerificationMethodTypeAgreement.JSON_WEB_KEY_2020.value
            or ver_method_type_str
            == VerificationMethodTypeAuthentication.JSON_WEB_KEY_2020.value
        ):
            if VerificationMethodField.JWK.value not in value:
                raise MalformedPeerDIDDocError(
                    "Invalid verification method: no {} field in {} method type".format(
                        VerificationMethodField.JWK.value, ver_method_type_str
                    )
                )
            return get_verification_method_type(
                value[VerificationMethodField.JWK.value]
            )

        try:
            return VerificationMethodTypeAgreement(ver_method_type_str)
        except ValueError:
            pass

        try:
            return VerificationMethodTypeAuthentication(ver_method_type_str)
        except ValueError:
            pass

        raise MalformedPeerDIDDocError(
            "Unknown verification method type {}".format(ver_method_type_str)
        )

    @classmethod
    def from_dict(cls, value: dict):
        if "id" not in value:
            raise MalformedPeerDIDDocError("No 'id' field in method {}".format(value))
        if "type" not in value:
            raise MalformedPeerDIDDocError("No 'type' field in method {}".format(value))

        ver_method_type = cls._get_ver_method_type(value)
        format, field = cls._get_public_key_format(ver_method_type)
        ver_material_cls = (
            VerificationMaterialAgreement
            if isinstance(ver_method_type, VerificationMethodTypeAgreement)
            else VerificationMaterialAuthentication
        )
        ver_material = ver_material_cls(
            value=value[field.value],
            format=format,
            type=ver_method_type,
        )

        return cls(
            id=value["id"], controller=value["controller"], ver_material=ver_material
        )


class DIDCommService:
    def __init__(
        self,
        id: str,
        service_endpoint: Optional[str],
        routing_keys: Optional[List[str]],
        accept: Optional[List[str]],
    ) -> None:
        self.id = id
        self.service_endpoint = service_endpoint
        self.routing_keys = routing_keys
        self.accept = accept

    @classmethod
    def from_dict(cls, values: dict):
        if not values:
            return values
        if not isinstance(values, list):
            return values

        res = []
        for value in values:
            if SERVICE_ID not in value:
                res.append(value)
                continue
            if SERVICE_TYPE not in value:
                res.append(value)
                continue

            service_type = value[SERVICE_TYPE]
            if service_type != SERVICE_DIDCOMM_MESSAGING:
                res.append(value)
                continue

            res.append(
                cls(
                    id=value[SERVICE_ID],
                    service_endpoint=value.get(SERVICE_ENDPOINT, None),
                    routing_keys=value.get(SERVICE_ROUTING_KEYS, None),
                    accept=value.get(SERVICE_ACCEPT, None),
                )
            )
        return res


Service = Union[Dict, DIDCommService]
