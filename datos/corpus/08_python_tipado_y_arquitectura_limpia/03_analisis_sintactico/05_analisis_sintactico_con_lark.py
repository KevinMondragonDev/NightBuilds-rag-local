"""
Tema 13 — Python tipado y arquitectura limpia | Lección 5: Análisis sintáctico con Lark
=========================================================================================

TIEMPO: 2.5 h · ANTES DE EMPEZAR: lecciones 1 a 3 y 01_core_python/03_python_avanzado/01_expresiones_regulares.py

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 05_analisis_sintactico_con_lark.py

    pip install lark

POR QUÉ IMPORTA: una expresión regular busca PATRONES dentro de un texto. Un
analizador sintáctico comprueba que TODO el texto tiene la ESTRUCTURA permitida y
lo convierte en datos con forma. Es la base de un validador serio de entradas, y
de la capa de seguridad que construirás en el NightBuild de esta sección.

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Qué diferencia hay entre el dominio y un adaptador?
    2. ¿Qué es la inyección de SQL y cómo la evitan los parámetros?
    3. ¿Qué hace re.search y qué NO te dice sobre el resto del texto?
"""

import unicodedata
from dataclasses import dataclass

from lark import Lark, Transformer, UnexpectedInput

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Una gramática: las reglas de lo que está permitido
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a describir un lenguaje pequeño en lugar de adivinar con patrones.
# CONCEPTO: una gramática dice de qué piezas (TOKENS, en mayúsculas) se compone
# un texto válido y cómo se combinan (reglas, en minúsculas). Aquí, un lenguaje de
# filtros: «monto > 500 y tipo = compra».

GRAMATICA = r"""
    ?consulta: condicion (CONECTOR condicion)*
    condicion: CAMPO OPERADOR valor
    ?valor: NUMERO | PALABRA

    CAMPO: "monto" | "tipo" | "categoria" | "cuenta"
    OPERADOR: ">=" | "<=" | "=" | ">" | "<"
    CONECTOR: "y" | "o"
    NUMERO: /\d+(\.\d+)?/
    PALABRA: /[a-záéíóúñ_]+/

    %import common.WS
    %ignore WS
"""
analizador = Lark(GRAMATICA, start="consulta", parser="lalr")

arbol = analizador.parse("monto > 500 y tipo = compra")
print("[paso 1]", str(arbol.data), [str(hijo.data) if hasattr(hijo, "data") else str(hijo) for hijo in arbol.children])
# SALIDA ESPERADA:
#   [paso 1] consulta ['condicion', 'y', 'condicion']

# 👉 TU TURNO 1: imprime arbol.pretty(). Añade a la gramática el campo «fecha» y
#    un valor de tipo fecha (AAAA-MM-DD), y analiza «fecha >= 2026-07-01».


# REFLEXIONA: CAMPO es una lista cerrada. ¿Qué pasa si alguien escribe
# «password = x»? Pruébalo antes de seguir.

# ════════════════════════════════════════════════════════════════════
# PASO 2 — Lo que no cumple la gramática, no entra
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: esta es la idea de seguridad. No haces una lista de cosas PROHIBIDAS
# (siempre faltará alguna): defines lo PERMITIDO y rechazas todo lo demás.
# Se llama lista blanca (allow-list), frente a lista negra.


def es_valida(texto: str) -> bool:
    try:
        analizador.parse(texto)
        return True
    except UnexpectedInput:
        return False


intentos = ["monto > 500", "monto > 500; DROP TABLE cuentas", "password = x", "tipo = compra o 1 = 1", "monto >"]
print("[paso 2]", [es_valida(t) for t in intentos])
# SALIDA ESPERADA:
#   [paso 2] [True, False, False, False, False]

# 👉 TU TURNO 2: captura UnexpectedInput y devuelve un mensaje útil: en qué columna
#    falló (error.column) y qué se esperaba. Un rechazo sin explicación frustra al
#    usuario legítimo.


# REFLEXIONA: una lista negra habría bloqueado «DROP TABLE». ¿Habría bloqueado
# «1 = 1»? ¿Y lo siguiente que se le ocurra a un atacante?

# ════════════════════════════════════════════════════════════════════
# PASO 3 — Del árbol a datos con tipo
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: el árbol es genérico. Un Transformer lo recorre de las hojas a la raíz
# y lo convierte en tus propios objetos, ya validados y tipados. A partir de aquí,
# el resto del programa trabaja con dataclasses, nunca con el texto original.


@dataclass(frozen=True)
class Condicion:
    campo: str
    operador: str
    valor: float | str


@dataclass(frozen=True)
class Consulta:
    condiciones: tuple[Condicion, ...]
    conectores: tuple[str, ...]


class AConsulta(Transformer):
    def NUMERO(self, token):
        return float(token)

    def PALABRA(self, token):
        return str(token)

    def condicion(self, hijos):
        campo, operador, valor = hijos
        return Condicion(str(campo), str(operador), valor)

    def consulta(self, hijos):
        return Consulta(tuple(h for h in hijos if isinstance(h, Condicion)),
                        tuple(str(h) for h in hijos if not isinstance(h, Condicion)))


def analizar(texto: str) -> Consulta:
    resultado = AConsulta().transform(analizador.parse(texto))
    return resultado if isinstance(resultado, Consulta) else Consulta((resultado,), ())


print("[paso 3]", analizar("monto > 500 y tipo = compra"))
# SALIDA ESPERADA:
#   [paso 3] Consulta(condiciones=(Condicion(campo='monto', operador='>', valor=500.0), Condicion(campo='tipo', operador='=', valor='compra')), conectores=('y',))

# 👉 TU TURNO 3: escribe a_sql(consulta) que devuelva un texto con marcadores y la
#    lista de parámetros, por ejemplo: ("monto > %s AND tipo = %s", [500.0, "compra"]).
#    Los valores NUNCA se pegan dentro del SQL.


# COMPRUEBA: a_sql(analizar("monto > 500 y tipo = compra")) devuelve exactamente eso.

# ════════════════════════════════════════════════════════════════════
# PASO 4 — Reglas que la gramática no puede expresar
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: la sintaxis dice si el texto tiene la FORMA correcta. Que tenga
# SENTIDO es otra comprobación (semántica) y se hace después, sobre los objetos.
# «tipo > 500» es sintácticamente válido y no significa nada.

NUMERICOS, TIPOS = {"monto", "cuenta"}, {"compra", "deposito", "retiro", "transferencia"}


def errores_de_sentido(consulta: Consulta) -> list[str]:
    errores = []
    for c in consulta.condiciones:
        if c.campo in NUMERICOS and not isinstance(c.valor, float):
            errores.append(f"{c.campo} necesita un número")
        if c.campo not in NUMERICOS and c.operador != "=":
            errores.append(f"{c.campo} solo admite '='")
        if c.campo == "tipo" and c.valor not in TIPOS:
            errores.append(f"tipo desconocido: {c.valor}")
    return errores


print("[paso 4]", errores_de_sentido(analizar("tipo > 500 y monto = mucho")))
# SALIDA ESPERADA:
#   [paso 4] ["tipo solo admite '='", 'tipo desconocido: 500.0', 'monto necesita un número']

# 👉 TU TURNO 4: añade un límite de complejidad: una consulta con más de 5
#    condiciones se rechaza. ¿Por qué es también una medida de seguridad?


# ════════════════════════════════════════════════════════════════════
# PASO 5 — Normalizar ANTES de analizar
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: dos textos que se VEN iguales pueden ser bytes distintos: letras de
# otro alfabeto idénticas a las latinas, caracteres invisibles, variantes de
# ancho. Un filtro que compara texto sin normalizar se burla con eso. Primero se
# normaliza (NFKC), se quitan los invisibles, y solo entonces se analiza.

INVISIBLES = dict.fromkeys(map(ord, "​‌‍⁠﻿"))


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKC", texto).translate(INVISIBLES).strip().lower()


disfrazado = "ｍｏｎｔｏ > 5​00"  # letras de ancho completo y un espacio de ancho cero
print("[paso 5]", es_valida(disfrazado), es_valida(normalizar(disfrazado)), repr(normalizar(disfrazado)))
# SALIDA ESPERADA:
#   [paso 5] False True 'monto > 500'

# 👉 TU TURNO 5: la «і» cirílica (U+0456) se ve igual que la «i» latina y NFKC no la
#    cambia. Escribe tiene_alfabetos_mezclados(texto) usando unicodedata.name(c)
#    y pruébala con «tіpo = compra».


# REFLEXIONA: normalizar arregla el caso de ancho completo pero no el cirílico.
# ¿Qué te dice eso sobre confiar en una sola defensa?

# ════════════════════════════════════════════════════════════════════
# LO QUE UN ANALIZADOR SINTÁCTICO PUEDE Y NO PUEDE HACER
# ════════════════════════════════════════════════════════════════════
#   PUEDE garantizar la estructura de una entrada que TÚ defines: filtros,
#   comandos, plantillas, formatos. Ahí es una defensa fuerte.
#   NO PUEDE entender la intención de un texto libre en lenguaje natural: una
#   frase que manipula a un modelo de lenguaje es gramaticalmente una frase normal.
#   Por eso, en el NightBuild, el análisis sintáctico es UNA capa de varias.

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Añade a tu NightBuilds-api-banco un parámetro `filtro` en GET /movimientos que
# acepte este lenguaje: normalizar -> analizar -> validar el sentido -> SQL con
# parámetros. Si algo falla, 422 con la columna del error.
# COMPRUEBA: los cinco intentos del paso 2 devuelven 200, 422, 422, 422 y 422.
