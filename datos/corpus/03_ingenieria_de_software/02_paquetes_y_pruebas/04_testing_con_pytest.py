"""
Tema 8 — Ingeniería de software | Lección 4: Testing con pytest
=================================================================

TIEMPO: 2 h · ANTES DE EMPEZAR: lección 3 (tu paquete limpiador)

CÓMO USAR ESTA LECCIÓN:
    Este archivo ES un archivo de tests. Ejecútalo con pytest:
        pytest 05_ingenieria_de_datos/03_ingenieria_de_software/02_paquetes_y_pruebas/04_testing_con_pytest.py -v
    Verás 11 tests en verde y 3 que se saltan: son tus «TU TURNO».
    En cada paso: lee el test, PREDICE si pasará, ejecútalo y después haz tu turno
    quitando la línea @pytest.mark.skip.

    pip install pytest pytest-cov

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Para qué sirve pip install -e . ?
    2. ¿Qué dos cosas dice un type hint y qué añade el docstring?
    3. Rompes una función sin querer. ¿Cómo te enteras hoy? ¿Y cuánto tardas?
"""

import pytest

# ── El código que vamos a probar (en tu proyecto estaría en limpiador/reglas.py) ──


def convertir_monto(texto):
    """Convierte '$1,200.50' en 1200.5. Devuelve None si está vacío."""
    if texto is None or texto.strip() == "":
        return None
    return float(texto.replace("$", "").replace(",", "").strip())


def quitar_duplicados(filas, clave="id"):
    if not filas:
        raise ValueError("no hay filas")
    vistos, resultado = set(), []
    for fila in filas:
        if fila[clave] not in vistos:
            vistos.add(fila[clave])
            resultado.append(fila)
    return resultado


def guardar(filas, ruta):
    ruta.write_text("\n".join(str(fila["id"]) for fila in filas), encoding="utf-8")


# ════════════════════════════════════════════════════════════════════
# PASO 1 — Un test: preparar, actuar, comprobar
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: la forma de todos los tests que escribirás.
# CONCEPTO: pytest ejecuta las funciones que empiezan por test_. Un test PREPARA
# unos datos pequeños, ACTÚA (llama a tu código) y COMPRUEBA con assert. El nombre
# del test dice qué comportamiento garantiza.


def test_quita_las_filas_con_id_repetido():
    filas = [{"id": 1}, {"id": 1}, {"id": 2}]      # preparar
    resultado = quitar_duplicados(filas)            # actuar
    assert resultado == [{"id": 1}, {"id": 2}]      # comprobar


def test_conserva_la_primera_aparicion():
    filas = [{"id": 1, "monto": 10}, {"id": 1, "monto": 99}]
    assert quitar_duplicados(filas)[0]["monto"] == 10


@pytest.mark.skip(reason="TU TURNO 1")
def test_respeta_otra_clave():
    # 👉 TU TURNO 1: comprueba que quitar_duplicados(filas, clave="cuenta") usa esa clave.
    ...


# REFLEXIONA: rompe quitar_duplicados a propósito (por ejemplo, borra el `not`).
# ¿Qué tests fallan? Un test que nunca puede fallar no sirve de nada.

# ════════════════════════════════════════════════════════════════════
# PASO 2 — El mismo test con muchos casos: parametrize
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: en lugar de copiar el test seis veces, das una tabla de
# (entrada, esperado). Cada fila es un test independiente con su propio resultado.


@pytest.mark.parametrize("texto, esperado", [
    ("300", 300.0),
    ("$1,200.50", 1200.5),
    ("  45.0 ", 45.0),
    ("", None),
    (None, None),
])
def test_convertir_monto(texto, esperado):
    assert convertir_monto(texto) == esperado


@pytest.mark.skip(reason="TU TURNO 2")
def test_convertir_monto_con_texto_invalido():
    # 👉 TU TURNO 2: ¿qué debería pasar con "diez"? Decide (¿excepción?, ¿None?),
    #    escribe el test y, si hace falta, cambia convertir_monto.
    ...


# REFLEXIONA: ¿qué casos de borde faltan en la tabla? Piensa en "-50", "1.200,50"
# y "$". Añádelos y decide qué debe devolver cada uno.

# ════════════════════════════════════════════════════════════════════
# PASO 3 — Probar que falla como debe: pytest.raises
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: que una función lance el error correcto ante una entrada mala también
# es comportamiento, y también se prueba.


def test_lista_vacia_lanza_error():
    with pytest.raises(ValueError, match="no hay filas"):
        quitar_duplicados([])


def test_fila_sin_la_clave_lanza_keyerror():
    with pytest.raises(KeyError):
        quitar_duplicados([{"otro": 1}])


# ════════════════════════════════════════════════════════════════════
# PASO 4 — Datos compartidos: fixtures
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un fixture es una función que prepara algo que varios tests necesitan.
# El test lo pide poniendo su NOMBRE como parámetro. Cada test recibe una copia
# nueva, así que no se estorban. tmp_path es un fixture incluido en pytest: una
# carpeta temporal que se borra sola.


@pytest.fixture
def transacciones():
    return [{"id": 1, "monto": "10"}, {"id": 2, "monto": "$20"}, {"id": 2, "monto": "$20"}]


def test_el_fixture_tiene_un_duplicado(transacciones):
    assert len(quitar_duplicados(transacciones)) == 2


def test_guardar_escribe_un_id_por_linea(transacciones, tmp_path):
    ruta = tmp_path / "salida.txt"
    guardar(transacciones, ruta)
    assert ruta.read_text(encoding="utf-8").splitlines() == ["1", "2", "2"]


@pytest.mark.skip(reason="TU TURNO 3")
def test_total_de_las_transacciones(transacciones):
    # 👉 TU TURNO 3: usando el fixture, quitar_duplicados y convertir_monto,
    #    comprueba que el total sin duplicados es 30.0 (usa pytest.approx).
    ...


# REFLEXIONA: ¿por qué 0.1 + 0.2 == 0.3 es False y qué resuelve pytest.approx?

# ════════════════════════════════════════════════════════════════════
# PASO 5 — ¿Qué me falta por probar? Cobertura
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: la cobertura dice qué líneas ejecutó algún test. Sirve para encontrar
# lo que NADIE prueba; no demuestra que lo probado esté bien.
#
# 👉 TU TURNO 4: en tu paquete limpiador, crea tests/test_reglas.py con al menos un
#    test por regla y ejecútalo con:
#        pytest --cov=limpiador --cov-report=term-missing
#    Añade un test para una de las líneas que aparezcan como «Missing».
#
# REFLEXIONA: ¿un 100 % de cobertura significa que el código no tiene errores?
# Pon un ejemplo con convertir_monto.

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# TDD: elige una regla que todavía NO hayas implementado (por ejemplo, detectar
# montos capturados en centavos). Escribe PRIMERO los tests, comprueba que fallan
# y solo después escribe la función hasta que pasen.
# COMPRUEBA: en tu historial de Git, el commit de los tests va antes que el de la
# función.
