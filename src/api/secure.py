"""Static current-Comix secure-module extraction and crypto.

This module intentionally contains no JavaScript engine, browser automation,
or browser-derived session state. It parses the published secure asset as
data, extracts its per-build byte transforms, and applies them in Python.
"""
from __future__ import annotations

import ast
import base64
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import unquote


class SecureModuleError(ValueError):
    """The published secure module is not a compatible build."""


@dataclass(frozen=True)
class Pass:
    table_b64: str
    key_b64: str
    seed: int

    @property
    def table(self) -> bytes:
        table = base64.b64decode(self.table_b64)
        if len(table) != 256 or len(set(table)) != 256:
            raise SecureModuleError("secure substitution table is invalid")
        return table

    @property
    def key(self) -> bytes:
        key = base64.b64decode(self.key_b64)
        if not key:
            raise SecureModuleError("secure substitution key is empty")
        return key


@dataclass(frozen=True)
class SecurePlan:
    signing_passes: tuple[Pass, Pass, Pass]
    response_passes: tuple[Pass, Pass, Pass]
    token_parameter: str
    request_separator: str


_ASSIGNMENT = re.compile(
    r"([\w$]+)\s*(\+?=)\s*"
    r'((?:"(?:\\.|[^"\\])*")|(?:\'(?:\\.|[^\'\\])*\'))'
)
_STATES = (9, 95, 76, 42, 98, 78, 84, 51, 52, 311)
_TABLE_KEY = "QHKXSH"


def _switch_cases(source: str, start: int) -> dict[int, str]:
    brace = source.find("{", start)
    if brace < 0:
        raise SecureModuleError("secure table builder has no switch body")
    depth = 0
    quote: str | None = None
    escaped = False
    found: list[tuple[int, int, int]] = []
    end = -1
    position = brace
    while position < len(source):
        char = source[position]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = position
                break
        elif depth == 1 and source.startswith("case ", position):
            number_end = position + 5
            while number_end < len(source) and source[number_end].isdigit():
                number_end += 1
            if number_end < len(source) and source[number_end] == ":":
                found.append((int(source[position + 5:number_end]), position, number_end + 1))
        position += 1
    if end < 0:
        raise SecureModuleError("secure table-builder switch is unterminated")
    return {
        number: source[body:found[index + 1][1] if index + 1 < len(found) else end]
        for index, (number, _case, body) in enumerate(found)
    }


def _decode_pool(source: str) -> list[str]:
    start = source.find("function а0()")
    finish = source.find("Υ.n8=", start)
    if start < 0 or finish < 0:
        raise SecureModuleError("unsupported secure-module table builder")
    builder = source[start:finish]
    cases = _switch_cases(builder, builder.find("switch(b8)"))
    if not all(state in cases for state in _STATES):
        raise SecureModuleError("secure table-builder state signature changed")

    values: dict[str, str] = {}
    for state in _STATES:
        for variable, operator, literal in _ASSIGNMENT.findall(cases[state]):
            try:
                value = ast.literal_eval(literal)
            except (SyntaxError, ValueError) as error:
                raise SecureModuleError(f"cannot parse table literal for {variable}") from error
            values[variable] = values.get(variable, "") + value if operator == "+=" else value

    required = ("w6", "Н5", "E_", "Y9", "О6", "К2", "r1", "α8")
    if any(key not in values for key in required):
        raise SecureModuleError("secure table-builder payload is incomplete")
    encoded = (
        values["w6"] + ":" + values["Н5"] + "+" + values["E_"] + values["Y9"]
        + values["О6"] + "!" + values["К2"] + "$" + values["r1"] + "." + values["α8"]
    )
    decoded = unquote(encoded)
    plaintext = "".join(
        chr(ord(char) ^ ord(_TABLE_KEY[index % len(_TABLE_KEY)]))
        for index, char in enumerate(decoded)
    )
    pool = plaintext.split(chr(96))
    if len(pool) < 400 or "X-Scramble-Hash" not in pool:
        raise SecureModuleError("decoded secure string table failed validation")
    return pool


def _post_bootstrap_pool(pool: list[str]) -> list[str]:
    output = list(pool)
    for count, keep in ((7, 6), (2, 1), (6, 5), (7, 6), (10, 8), (8, 6)):
        tail = output[-count:]
        del output[-count:]
        output[0:0] = tail[:keep]
    return output


def _lookup(pool: list[str], number: int, rotation: int) -> str:
    index = number - 27
    offset = 0 if index <= 61 else 1 if index <= 310 else 2
    return pool[(index - offset + rotation) % len(pool)]


def extract_plan(source: str) -> SecurePlan:
    """Extract current request signing and response decode configuration."""
    pool = _post_bootstrap_pool(_decode_pool(source))
    base64_values: dict[str, bytes] = {}
    for value in pool:
        try:
            base64_values[value] = base64.b64decode(value, validate=True)
        except (ValueError, TypeError):
            continue
    tables = {
        value for value, decoded in base64_values.items()
        if len(decoded) == 256 and len(set(decoded)) == 256
    }
    keys = {value for value, decoded in base64_values.items() if len(decoded) in (24, 32)}
    table_indices = (413, 205, 420)
    key_indices = (225, 230, 349)
    rotations = [
        rotation for rotation in range(len(pool))
        if all(_lookup(pool, number, rotation) in tables for number in table_indices)
        and all(_lookup(pool, number, rotation) in keys for number in key_indices)
    ]
    if len(rotations) != 1:
        raise SecureModuleError(f"could not uniquely resolve secure table rotation: {rotations!r}")
    rotation = rotations[0]
    signing = tuple(
        Pass(_lookup(pool, table_index, rotation), _lookup(pool, key_index, rotation), seed)
        for table_index, key_index, seed in zip(table_indices, key_indices, (189, 133, 32))
    )
    return SecurePlan(
        signing_passes=signing,
        response_passes=tuple(reversed(signing)),
        token_parameter=_lookup(pool, 240, rotation),
        request_separator=_lookup(pool, 74, rotation),
    )


def _forward(data: bytes, config: Pass) -> bytes:
    output = bytearray(len(data))
    previous = config.seed & 0xFF
    table, key = config.table, config.key
    for index, value in enumerate(data):
        transformed = table[value ^ key[index % len(key)] ^ previous]
        output[index] = transformed
        previous = transformed
    return bytes(output)


def _reverse(data: bytes, config: Pass) -> bytes:
    inverse = bytearray(256)
    for index, value in enumerate(config.table):
        inverse[value] = index
    output = bytearray(len(data))
    previous = config.seed & 0xFF
    key = config.key
    for index, value in enumerate(data):
        output[index] = inverse[value] ^ key[index % len(key)] ^ previous
        previous = value
    return bytes(output)


def _canonical_params(params: Mapping[str, Any], token_parameter: str) -> str:
    pairs: list[str] = []

    def visit(prefix: str, value: Any) -> None:
        if value is None:
            return
        if isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                visit(f"{prefix}[{index}]", item)
        elif isinstance(value, Mapping):
            for key in sorted(value):
                visit(str(key) if not prefix else f"{prefix}[{key}]", value[key])
        else:
            pairs.append(f"{prefix}={json.dumps(value, ensure_ascii=False, separators=(',', ':'))}")

    for key in sorted(params):
        if key != token_parameter:
            visit(str(key), params[key])
    return "&".join(pairs)


def signed_token(url_or_path: str, params: Mapping[str, Any], plan: SecurePlan) -> str:
    """Return the secure interceptor's signed query parameter value."""
    path = re.sub(r"^https?://[^/]+", "", url_or_path)
    path = re.sub(r"^/api/v1", "", path)
    encoded_params = _canonical_params(params, plan.token_parameter)
    value = path + (plan.request_separator + encoded_params if encoded_params else "")
    data = value.encode("utf-8")
    for config in plan.signing_passes:
        data = _forward(data, config)
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def decrypt_response(value: str, plan: SecurePlan) -> dict[str, Any]:
    """Decode an x-enc response and return the Axios-equivalent result value."""
    data = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    for config in plan.response_passes:
        data = _reverse(data, config)
    decoded = json.loads(data.decode("utf-8"))
    if isinstance(decoded, dict) and decoded.get("status") == "ok" and "result" in decoded:
        return decoded["result"]
    return decoded
