"""Normalización y validación de números de teléfono de clientes (Colombia).

Reglas:
- Se limpia todo lo que no sea dígito (espacios, guiones, paréntesis).
- Si no trae indicativo de país, se asume Colombia (+57).
- Se normaliza a formato E.164 (+<indicativo><número>).
- Se rechazan valores vacíos, centinela (todos los dígitos iguales, ej.
  "0000000000") y longitudes distintas a 10 dígitos locales: desde el plan
  de numeración unificado de la CRC (2021), tanto celular (ej. 3001234567)
  como fijo con indicativo de área (ej. 6011234567) usan 10 dígitos.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

PAIS_DEFAULT = "57"
LARGO_LOCAL = 10


@dataclass
class ResultadoValidacion:
    valido: bool
    telefono_normalizado: str | None
    motivo_rechazo: str | None


def _solo_digitos(raw: str) -> str:
    return re.sub(r"\D", "", raw or "")


def _es_centinela(digitos: str) -> bool:
    return len(set(digitos)) <= 1


def normalizar_telefono(raw: str, pais_default: str = PAIS_DEFAULT) -> ResultadoValidacion:
    digitos = _solo_digitos(raw)

    if not digitos:
        return ResultadoValidacion(False, None, "vacío o sin dígitos")

    if _es_centinela(digitos):
        return ResultadoValidacion(False, None, "valor centinela (todos los dígitos iguales)")

    # Ya viene con indicativo de país (ej. 57300... o 0057300...)
    if digitos.startswith("00" + pais_default):
        digitos = digitos[2:]
    if digitos.startswith(pais_default) and len(digitos) > LARGO_LOCAL:
        local = digitos[len(pais_default):]
    else:
        local = digitos

    if len(local) != LARGO_LOCAL:
        return ResultadoValidacion(False, None, f"longitud inválida ({len(local)} dígitos locales)")

    return ResultadoValidacion(True, f"+{pais_default}{local}", None)
