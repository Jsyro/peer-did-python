from enum import Enum
from typing import Tuple

import varint

from peerdid.types import VerificationMethodType, VerificationMethodTypeAgreement


class Codec(Enum):
    X25519 = 0xEC
    ED25519 = 0xED


def to_multicodec(value: bytes, key_type: VerificationMethodType) -> bytes:
    codec = _get_codec(key_type)
    prefix = varint.encode(codec.value)
    return b"".join([prefix, value])


def from_multicodec(value: bytes) -> Tuple[bytes, Codec]:
    try:
        prefix_int = varint.decode_bytes(value)
    except TypeError:
        raise ValueError("Invalid multicodec prefix in {}".format(str(value)))

    try:
        codec = Codec(prefix_int)
    except ValueError:
        raise ValueError(
            "Unknown multicodec prefix {} in {}".format(str(prefix_int), str(value))
        )

    prefix = varint.encode(prefix_int)
    return value[len(prefix) :], codec


def _get_codec(key_type: VerificationMethodType) -> Codec:
    if isinstance(key_type, VerificationMethodTypeAgreement):
        return Codec.X25519
    else:
        return Codec.ED25519
