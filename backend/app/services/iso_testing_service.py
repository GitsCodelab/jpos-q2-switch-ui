from __future__ import annotations

import os
import re
import socket
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status


SWITCH_HOST = os.getenv("SWITCH_HOST", "switch")
SWITCH_PORT = int(os.getenv("SWITCH_PORT", "9000"))
SWITCH_TIMEOUT = float(os.getenv("SWITCH_TIMEOUT", "10"))

# In-memory history — cleared on restart (no DB persistence)
_history: deque[dict[str, Any]] = deque(maxlen=20)

DEFAULT_ISO_MESSAGE: dict[str, str] = {
	"mti": "0200",
	"3": "000000",
	"4": "000000000100",
	"11": "123456",
	"37": "123456789012",
	"41": "TERM0001",
	"2": "1234567890123456",
}

PROFILES: dict[str, dict[str, Any]] = {
	"atm": {
		"mti": "0200",
		"fields": {
			"3": "011000",
			"4": "000000010000",
			"22": "021",
			"41": "ATM0001",
		},
		"description": "ATM withdrawal transaction",
	},
	"pos": {
		"mti": "0200",
		"fields": {
			"3": "000000",
			"4": "000000005000",
			"22": "022",
			"41": "POS0001",
		},
		"description": "POS purchase transaction",
	},
	"reversal": {
		"mti": "0420",
		"fields": {
			"3": "000000",
			"4": "000000001000",
			"11": "654321",
			"37": "987654321098",
			"41": "TERM-REV",
		},
		"description": "Transaction reversal request",
	},
	"fraud": {
		"mti": "0200",
		"fields": {
			"3": "000000",
			"4": "000000999999",
			"22": "029",
			"41": "TERM9999",
			"2": "9999999999999999",
		},
		"description": "High-risk fraud test transaction",
	},
	"custom": {
		"mti": None,
		"fields": {},
		"description": "Manual field entry — operator fills all values",
	},
}

_MTI_PATTERN = re.compile(r"^\d{4}$")
_FIELD_NUMBER_PATTERN = re.compile(r"^(?:[2-9]|[1-9]\d|1[01]\d|12[0-8])$")


def get_profiles() -> dict[str, dict[str, Any]]:
	return PROFILES


def _normalized_profile_name(profile: str | None) -> str:
	candidate = (profile or "custom").strip().lower() or "custom"
	if candidate not in PROFILES:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown profile: {candidate}")
	return candidate


def _validate_mti(mti: str) -> str:
	value = str(mti).strip()
	if not _MTI_PATTERN.fullmatch(value):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MTI must be a 4-digit numeric string")
	return value


def _validate_fields(fields: dict[str, str]) -> dict[str, str]:
	normalized: dict[str, str] = {}
	for key, value in fields.items():
		normalized_key = str(key).strip()
		normalized_value = str(value)
		if normalized_key == "mti":
			normalized[normalized_key] = _validate_mti(normalized_value)
			continue

		if not _FIELD_NUMBER_PATTERN.fullmatch(normalized_key):
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"Invalid ISO field key: {normalized_key}",
			)
		normalized[normalized_key] = normalized_value

	if "4" in normalized and not re.fullmatch(r"\d{12}", normalized["4"]):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Field 4 must be a 12-digit zero-padded string",
		)
	return normalized


def _build_request_message(profile: str, fields: dict[str, str]) -> dict[str, str]:
	message = dict(DEFAULT_ISO_MESSAGE)

	if profile != "custom":
		profile_meta = PROFILES[profile]
		if profile_meta.get("mti"):
			message["mti"] = str(profile_meta["mti"])
		for key, value in profile_meta.get("fields", {}).items():
			message[str(key)] = str(value)

	for key, value in fields.items():
		message[key] = value

	if "mti" not in message:
		message["mti"] = DEFAULT_ISO_MESSAGE["mti"]

	message["mti"] = _validate_mti(message["mti"])
	return message


# ---------------------------------------------------------------------------
# ISO8583 binary packer/unpacker for jPOS GenericPackager (iso87.xml)
# Field type key:
#   BCD   = IFB_NUMERIC  – BCD packed, fixed length (ceil(N/2) bytes)
#   CHAR  = IF_CHAR      – ASCII fixed length
#   LLNUM = IFB_LLNUM    – 1-byte BCD digit-count prefix + BCD data
# ---------------------------------------------------------------------------
_FIELD_SPEC: dict[int, tuple[str, int]] = {
	2:  ("LLNUM", 19),
	3:  ("BCD",   6),
	4:  ("BCD",  12),
	5:  ("BCD",  12),
	6:  ("BCD",  12),
	7:  ("BCD",  10),
	11: ("BCD",   6),
	12: ("BCD",   6),
	13: ("BCD",   4),
	14: ("BCD",   4),
	22: ("BCD",   3),
	37: ("CHAR", 12),
	38: ("CHAR",  6),
	39: ("BCD",   2),
	41: ("CHAR",  8),
	42: ("CHAR", 15),
}


def _bcd_pack(digits: str, field_length: int) -> bytes:
	"""Pack a decimal digit string as BCD into ceil(field_length/2) bytes."""
	byte_len = (field_length + 1) // 2
	# Pad with a leading zero nibble when field_length is odd
	padded = digits.zfill(byte_len * 2)
	return bytes.fromhex(padded)


def _pack_field(field_id: int, value: str) -> bytes:
	ftype, flength = _FIELD_SPEC[field_id]
	if ftype == "BCD":
		return _bcd_pack(value.zfill(flength), flength)
	if ftype == "CHAR":
		return value.encode("ascii").ljust(flength)[:flength]
	if ftype == "LLNUM":
		digit_count = len(value)
		length_byte = bytes.fromhex(f"{digit_count:02d}")
		byte_len = (digit_count + 1) // 2
		padded = value if digit_count % 2 == 0 else "0" + value
		return length_byte + bytes.fromhex(padded)
	raise ValueError(f"Unknown field type: {ftype}")  # pragma: no cover


def _pack_iso_message(message: dict[str, str]) -> bytes:
	"""Produce a binary ISO8583 message (MTI + bitmap + fields)."""
	mti = message.get("mti", "0200")
	mti_bytes = bytes.fromhex(mti)

	numeric_fields = {int(k): v for k, v in message.items() if k != "mti"}

	bitmap = 0
	for fid in numeric_fields:
		if 1 <= fid <= 64:
			bitmap |= 1 << (64 - fid)
	bitmap_bytes = bitmap.to_bytes(8, "big")

	field_data = b""
	for fid in sorted(numeric_fields):
		if fid in _FIELD_SPEC:
			field_data += _pack_field(fid, numeric_fields[fid])

	return mti_bytes + bitmap_bytes + field_data


def _recv_exactly(sock: socket.socket, n: int) -> bytes:
	buf = b""
	while len(buf) < n:
		chunk = sock.recv(n - len(buf))
		if not chunk:
			raise ConnectionError("Switch closed connection before response was complete")
		buf += chunk
	return buf


def _unpack_iso_response(data: bytes) -> dict[str, str | None]:
	"""Unpack the binary ISO8583 response sent by jPOS over ASCIIChannel."""
	result: dict[str, str | None] = {"mti": None, "rc": None, "stan": None, "rrn": None}
	if len(data) < 10:
		return result

	result["mti"] = data[0:2].hex()  # e.g. b'\x02\x10' → "0210"
	bitmap = int.from_bytes(data[2:10], "big")
	pos = 10

	for fid in range(1, 65):
		if not (bitmap & (1 << (64 - fid))):
			continue
		if fid not in _FIELD_SPEC:
			break  # unknown field — cannot advance cursor safely

		ftype, flength = _FIELD_SPEC[fid]
		if ftype == "BCD":
			byte_len = (flength + 1) // 2
			raw = data[pos: pos + byte_len]
			pos += byte_len
			hex_str = raw.hex()
			if flength % 2 == 1:
				hex_str = hex_str[1:]  # strip leading padding nibble
			if fid == 39:
				result["rc"] = hex_str
			elif fid == 11:
				result["stan"] = hex_str
		elif ftype == "CHAR":
			raw = data[pos: pos + flength]
			pos += flength
			value = raw.decode("ascii", errors="replace").strip()
			if fid == 37:
				result["rrn"] = value
		elif ftype == "LLNUM":
			digit_count = int(data[pos: pos + 1].hex())
			pos += 1
			pos += (digit_count + 1) // 2

	return result


def _send_via_socket(message: dict[str, str]) -> tuple[dict[str, str | None], str, str]:
	"""Connect to the jPOS switch over TCP and exchange an ISO8583 message.

	Returns (parsed_response, request_hex, response_hex).
	"""
	packed = _pack_iso_message(message)
	request_hex = packed.hex()
	# jPOS ASCIIChannel framing: 4-byte ASCII decimal length header
	wire = f"{len(packed):04d}".encode("ascii") + packed

	try:
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.settimeout(SWITCH_TIMEOUT)
			sock.connect((SWITCH_HOST, SWITCH_PORT))
			sock.sendall(wire)
			raw_len = _recv_exactly(sock, 4)
			resp_len = int(raw_len.decode("ascii").strip())
			resp_data = _recv_exactly(sock, resp_len)
	except (ConnectionRefusedError, OSError) as exc:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail=f"Switch connection failed: {exc}",
		)
	except TimeoutError as exc:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail=f"Switch timed out: {exc}",
		)

	return _unpack_iso_response(resp_data), request_hex, resp_data.hex()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_iso_test(profile: str | None, fields: dict[str, Any] | None) -> dict[str, Any]:
	chosen_profile = _normalized_profile_name(profile)
	normalized_fields = _validate_fields({str(k): str(v) for k, v in (fields or {}).items() if v is not None})
	request_message = _build_request_message(chosen_profile, normalized_fields)

	started_at = datetime.now(timezone.utc)
	start = time.perf_counter()
	parsed_response, request_hex, response_hex = _send_via_socket(request_message)
	elapsed_ms = int((time.perf_counter() - start) * 1000)

	rc = parsed_response.get("rc")
	payload: dict[str, Any] = {
		"success": rc == "00",
		"request": {
			"mti": request_message.get("mti"),
			"fields": {k: v for k, v in request_message.items() if k != "mti"},
		},
		"response": {
			"mti": parsed_response.get("mti"),
			"rc": rc,
			"stan": parsed_response.get("stan"),
			"rrn": parsed_response.get("rrn"),
			"fields": {
				"39": rc,
				"11": parsed_response.get("stan"),
				"37": parsed_response.get("rrn"),
			},
		},
		"elapsed_ms": elapsed_ms,
		"sent_at": started_at.isoformat(),
		"profile": chosen_profile,
		"raw": {
			"request_hex": request_hex,
			"response_hex": response_hex,
		},
	}

	_history.appendleft(payload)
	return payload


def get_history(limit: int = 20) -> dict[str, Any]:
	entries = list(_history)[:limit]
	return {"count": len(entries), "history": entries}
