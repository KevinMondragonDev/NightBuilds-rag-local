"""
Tema 13 — Python tipado y arquitectura limpia | Lección 3: Arquitectura limpia
================================================================================

TIEMPO: 2.5 h · ANTES DE EMPEZAR: lección 2, 05_patrones_de_diseno (01 y 02) y 06_apis_con_fastapi/01_construir/03

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 03_arquitectura_limpia.py

    Todo está en un solo archivo para que veas las capas juntas. En la lección 4
    cada capa pasa a su carpeta.

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Qué es un Protocol y quién comprueba que una clase lo cumple?
    2. Inyección de dependencias en una frase.
    3. En la API por capas, ¿por qué el servicio no lanzaba HTTPException?

LA IDEA EN UNA FRASE:
    Las reglas del negocio no dependen de nada; todo lo demás depende de ellas.

        ┌──────────────────────────────────────────────────────┐
        │  INFRAESTRUCTURA   FastAPI, PostgreSQL, S3, archivos  │
        │   ┌──────────────────────────────────────────────┐   │
        │   │  CASOS DE USO   qué hace la aplicación        │   │
        │   │   ┌──────────────────────────────────────┐   │   │
        │   │   │  DOMINIO   entidades y reglas        │   │   │
        │   │   └──────────────────────────────────────┘   │   │
        │   └──────────────────────────────────────────────┘   │
        └──────────────────────────────────────────────────────┘
        Regla de dependencia: las flechas de import solo apuntan HACIA DENTRO.
"""

from dataclasses import dataclass
from typing import NewType, Protocol

# ════════════════════════════════════════════════════════════════════
# PASO 1 — El dominio: reglas que no saben nada del mundo exterior
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a separar lo que es del NEGOCIO de lo que es de la TECNOLOGÍA.
# CONCEPTO: el dominio son las entidades y sus reglas. No importa FastAPI, ni SQL,
# ni pandas, ni archivos: solo Python. Si mañana cambia la base de datos, esta
# parte no se toca. Por eso es lo más fácil de probar y lo que más dura.

CuentaId = NewType("CuentaId", int)


class SaldoInsuficiente(Exception): ...


class CuentaNoExiste(Exception): ...


@dataclass(frozen=True)
class Cuenta:
    id: CuentaId
    saldo: float
    limite_diario: float = 10_000.0

    def retirar(self, monto: float) -> "Cuenta":
        if monto <= 0:
            raise ValueError("el monto debe ser positivo")
        if monto > self.limite_diario:
            raise ValueError("supera el límite diario")
        if monto > self.saldo:
            raise SaldoInsuficiente(self.id)
        return Cuenta(self.id, round(self.saldo - monto, 2), self.limite_diario)  # inmutable: devuelve otra


print("[paso 1]", Cuenta(CuentaId(1), 500.0).retirar(120.0))
# SALIDA ESPERADA:
#   [paso 1] Cuenta(id=1, saldo=380.0, limite_diario=10000.0)

# 👉 TU TURNO 1: añade al dominio el método depositar(monto). Escribe tres assert
#    que prueben retirar y depositar. Fíjate: no necesitas base de datos, ni API,
#    ni un solo objeto falso.


# REFLEXIONA: `retirar` devuelve una Cuenta nueva en lugar de modificar la
# existente. ¿Qué errores evita eso?

# ════════════════════════════════════════════════════════════════════
# PASO 2 — Los puertos: lo que el negocio NECESITA, sin decir quién lo da
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: el caso de uso necesita guardar cuentas y avisar de un retiro. Declara
# esas necesidades como contratos (Protocol) y se las pasan desde fuera. Son los
# «puertos». Fíjate en la dirección: el contrato lo define quien lo NECESITA.


class RepositorioCuentas(Protocol):
    def obtener(self, cuenta: CuentaId) -> Cuenta | None: ...
    def guardar(self, cuenta: Cuenta) -> None: ...


class Notificador(Protocol):
    def avisar(self, cuenta: CuentaId, mensaje: str) -> None: ...


# ════════════════════════════════════════════════════════════════════
# PASO 3 — El caso de uso: una acción de la aplicación
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un caso de uso es UNA cosa que alguien puede pedirle al sistema. Su
# trabajo es coordinar: traer la entidad, pedirle que aplique su regla, guardar y
# avisar. No decide reglas (eso es dominio) ni sabe de HTTP o SQL (eso es infraestructura).


@dataclass(frozen=True)
class RetirarDinero:
    cuentas: RepositorioCuentas
    notificador: Notificador

    def ejecutar(self, cuenta_id: CuentaId, monto: float) -> float:
        cuenta = self.cuentas.obtener(cuenta_id)
        if cuenta is None:
            raise CuentaNoExiste(cuenta_id)
        actualizada = cuenta.retirar(monto)  # la regla vive en el dominio
        self.cuentas.guardar(actualizada)
        self.notificador.avisar(cuenta_id, f"Retiro de {monto:.2f}")
        return actualizada.saldo


# ════════════════════════════════════════════════════════════════════
# PASO 4 — Los adaptadores: la tecnología concreta, en el borde
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un adaptador implementa un puerto con una tecnología. Aquí, memoria
# y pantalla. En producción, PostgreSQL y correo. El caso de uso no cambia.


class CuentasEnMemoria:
    def __init__(self, cuentas: list[Cuenta]) -> None:
        self._cuentas = {c.id: c for c in cuentas}

    def obtener(self, cuenta: CuentaId) -> Cuenta | None:
        return self._cuentas.get(cuenta)

    def guardar(self, cuenta: Cuenta) -> None:
        self._cuentas[cuenta.id] = cuenta


class NotificadorEnLista:
    def __init__(self) -> None:
        self.enviados: list[str] = []

    def avisar(self, cuenta: CuentaId, mensaje: str) -> None:
        self.enviados.append(f"[cuenta {cuenta}] {mensaje}")


# ════════════════════════════════════════════════════════════════════
# PASO 5 — La raíz de composición: el único sitio que conoce todo
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: alguien tiene que decidir qué adaptador se usa. Ese sitio es UNO, está
# en el borde más externo (main, o el arranque de la API) y es el único que
# importa de todas las capas.

repositorio = CuentasEnMemoria([Cuenta(CuentaId(1), 500.0), Cuenta(CuentaId(2), 50.0)])
notificador = NotificadorEnLista()
retirar = RetirarDinero(repositorio, notificador)

print("[paso 5]", retirar.ejecutar(CuentaId(1), 120.0), notificador.enviados)
try:
    retirar.ejecutar(CuentaId(2), 300.0)
except SaldoInsuficiente:
    print("[paso 5] saldo insuficiente | avisos enviados:", len(notificador.enviados))
# SALIDA ESPERADA:
#   [paso 5] 380.0 ['[cuenta 1] Retiro de 120.00']
#   [paso 5] saldo insuficiente | avisos enviados: 1

# 👉 TU TURNO 2: escribe el caso de uso Transferir(origen, destino, monto) usando
#    solo el dominio y los puertos.

# 👉 TU TURNO 3: escribe un adaptador CuentasEnPostgres con psycopg y otro
#    NotificadorEnConsola. Cambia la raíz de composición para usarlos.
#    COMPRUEBA: no tocaste ni una línea del dominio ni del caso de uso.

# 👉 TU TURNO 4: conecta el caso de uso a FastAPI: un endpoint que reciba el JSON,
#    llame a retirar.ejecutar y traduzca cada excepción de dominio a su código HTTP.


# REFLEXIONA:
#   - Si falla `avisar` después de `guardar`, el dinero ya salió y nadie fue
#     avisado. ¿En qué capa se resuelve eso?
#   - ¿Qué archivos tocarías para: cambiar el límite diario, cambiar de base de
#     datos, añadir un aviso por SMS? Debe ser UNA capa en cada caso.

# ════════════════════════════════════════════════════════════════════
# CUÁNDO **NO** HACE FALTA
# ════════════════════════════════════════════════════════════════════
#   Un script de 80 líneas que se ejecuta una vez no necesita cuatro capas.
#   Compensa cuando hay reglas de negocio que cambian, más de una entrada (API,
#   línea de comandos, un job) o más de una tecnología posible detrás.
#   Señal de que te pasaste: clases que solo reenvían la llamada a otra clase.

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Reorganiza tu NightBuilds-api-banco con esta arquitectura. Los routers pasan a
# ser adaptadores de entrada, los repositorios adaptadores de salida, y las reglas
# que hoy viven en los servicios se mueven a las entidades del dominio.
# COMPRUEBA: los tests del dominio y de los casos de uso pasan sin instalar
# FastAPI ni psycopg.
