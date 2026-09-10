import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.normalizar import normalizar_telefono


def test_celular_local_simple():
    r = normalizar_telefono("3001234567")
    assert r.valido
    assert r.telefono_normalizado == "+573001234567"


def test_celular_con_espacios_y_guiones():
    r = normalizar_telefono("300 123-4567")
    assert r.valido
    assert r.telefono_normalizado == "+573001234567"


def test_celular_con_indicativo_pais():
    r = normalizar_telefono("+57 300 123 4567")
    assert r.valido
    assert r.telefono_normalizado == "+573001234567"


def test_celular_con_indicativo_00():
    r = normalizar_telefono("0057 3001234567")
    assert r.valido
    assert r.telefono_normalizado == "+573001234567"


def test_fijo_con_indicativo_area():
    r = normalizar_telefono("(601) 123-4567")
    assert r.valido
    assert r.telefono_normalizado == "+576011234567"


def test_vacio_se_rechaza():
    r = normalizar_telefono("")
    assert not r.valido
    assert "vacío" in r.motivo_rechazo


def test_centinela_se_rechaza():
    r = normalizar_telefono("0000000000")
    assert not r.valido
    assert "centinela" in r.motivo_rechazo


def test_longitud_invalida_se_rechaza():
    r = normalizar_telefono("12345")
    assert not r.valido
    assert "longitud" in r.motivo_rechazo


def test_valor_no_numerico_se_rechaza():
    r = normalizar_telefono("no tiene telefono")
    assert not r.valido
