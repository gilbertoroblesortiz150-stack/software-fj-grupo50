"""Software FJ - verificacion reproducible de los puntos 1, 2, 3 y 5.

Ejecutar desde la carpeta que contiene los archivos .py del proyecto:
    python pruebas_integracion.py

El punto 4 (clase_reserva.py) se revisa por separado: esta prueba no
supone conocer su interfaz ni reemplaza la integracion final de Reserva.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from typing import Callable

from clase_abstracta_general import (
    EntidadBase,
    ErrorValidacionDato,
    ErrorOperacionNoPermitida,
    ErrorServicioNoDisponible,
)
from clase_cliente import Cliente
from clase_servicios import ReservaSala, AlquilerEquipo, AsesoriaEspecializada
from calculador_costos import CalculadorCostos


@dataclass
class Resultado:
    numero: int
    nombre: str
    correcto: bool
    detalle: str


def _debe_fallar(accion: Callable[[], object], error_esperado: type[Exception]) -> None:
    """Comprueba que una operacion invalida produzca la excepcion esperada."""
    try:
        accion()
    except error_esperado:
        return
    raise AssertionError(f"Se esperaba {error_esperado.__name__} y no ocurrio")


def ejecutar_simulaciones() -> list[Resultado]:
    registros: list[Resultado] = []
    cliente = None
    sala = None
    equipo = None
    asesoria = None
    calculador = None

    def verificar(nombre: str, accion: Callable[[], object]) -> None:
        numero = len(registros) + 1
        try:
            salida = accion()
        except Exception as exc:
            registros.append(Resultado(numero, nombre, False, f"{type(exc).__name__}: {exc}"))
        else:
            registros.append(Resultado(numero, nombre, True, str(salida or "Correcto")))

    def caso1():
        nonlocal cliente
        cliente = Cliente("C-001", "Felipe Jimenez", "felipe@example.com", "3001234567", "1090456789", "clave123")
        assert isinstance(cliente, EntidadBase)
        assert cliente.nombre == "Felipe Jimenez"
        return cliente.resumen()

    def caso2():
        assert cliente is not None
        assert cliente.verificar("clave123")
        assert not cliente.verificar("incorrecta")
        return "Verificacion de clave valida e invalida"

    def caso3():
        _debe_fallar(lambda: Cliente("C-002", "Ana Lopez", "correo-sin-arroba", "3001234567", "12345678", "123"), ErrorValidacionDato)
        return "Correo invalido rechazado"

    def caso4():
        nonlocal sala
        sala = ReservaSala("S-001", "Sala de reuniones", 70000, capacidad_maxima=10)
        total = sala.calcular_costo(3, impuesto_pct=19, descuento_pct=10, asistentes=6)
        assert total == 224910.0, total
        return f"Sala por 3 horas: ${total:,.2f}"

    def caso5():
        assert sala is not None
        _debe_fallar(lambda: sala.calcular_costo(1, asistentes=11), ErrorOperacionNoPermitida)
        return "Aforo excedido rechazado"

    def caso6():
        nonlocal equipo
        equipo = AlquilerEquipo("E-001", "Video proyector", 40000, unidades_disponibles=4)
        total = equipo.calcular_costo(2, impuesto_pct=19, descuento_pct=5, cantidad=2)
        assert total == 180880.0, total
        return f"2 equipos por 2 dias: ${total:,.2f}"

    def caso7():
        assert equipo is not None
        _debe_fallar(lambda: equipo.calcular_costo(1, cantidad=9), ErrorServicioNoDisponible)
        return "Alquiler sin stock suficiente rechazado"

    def caso8():
        nonlocal asesoria
        asesoria = AsesoriaEspecializada("A-001", "Asesoria en Python", 120000, "Programacion")
        total = asesoria.calcular_costo(2, impuesto_pct=19)
        assert total == 285600.0, total
        return f"Asesoria por 2 horas: ${total:,.2f}"

    def caso9():
        nonlocal calculador
        calculador = CalculadorCostos()
        total = calculador.calcular(100000)
        assert total == 119000.0, total
        return f"Cotizacion IVA 19%: ${total:,.2f}"

    def caso10():
        assert calculador is not None
        total = calculador.calcular(100000, descuento_pct=20)
        assert total == 95200.0, total
        return f"Cotizacion con 20% de descuento: ${total:,.2f}"

    def caso11():
        assert calculador is not None
        # Se captura el tipo de excepcion del modulo que lo define. El
        # punto 5 trae temporalmente excepciones de dominio propias.
        from calculador_costos import ErrorCalculoInconsistente
        _debe_fallar(lambda: calculador.calcular(100000, descuento_pct=110), ErrorCalculoInconsistente)
        return "Descuento mayor al 100% rechazado"

    def caso12():
        assert sala is not None
        sala.cambiar_disponibilidad(False)
        assert not sala.disponible
        sala.cambiar_disponibilidad(True)
        assert sala.disponible
        return "Disponibilidad desactivada y reactivada"

    def caso13():
        assert equipo is not None
        equipo.consumir_unidades(2)
        assert equipo.unidades_disponibles == 2
        return "Inventario descontado: quedan 2 equipos"

    def caso14():
        assert cliente is not None
        cliente.desactivar()
        assert not cliente.activa
        cliente.activar()
        assert cliente.activa
        return "Cliente desactivado y reactivado"

    escenarios = [
        ("Crear cliente valido", caso1),
        ("Verificar contrasena", caso2),
        ("Rechazar correo invalido", caso3),
        ("Costo de sala", caso4),
        ("Rechazar exceso de aforo", caso5),
        ("Costo de alquiler", caso6),
        ("Rechazar falta de inventario", caso7),
        ("Costo de asesoria", caso8),
        ("IVA de cotizacion", caso9),
        ("Descuento de cotizacion", caso10),
        ("Rechazar descuento imposible", caso11),
        ("Cambiar disponibilidad", caso12),
        ("Consumir inventario", caso13),
        ("Activar y desactivar cliente", caso14),
    ]
    for nombre, accion in escenarios:
        verificar(nombre, accion)
    return registros


def verificar_reserva() -> str:
    """Informa si el modulo Reserva existe; no presume su firma ni lo reemplaza."""
    try:
        modulo = importlib.import_module("clase_reserva")
    except ModuleNotFoundError as exc:
        if exc.name == "clase_reserva":
            return "Punto 4: el archivo clase_reserva.py no esta en esta carpeta."
        return f"Punto 4: falta la dependencia {exc.name!r} requerida por Reserva."
    except Exception as exc:
        return f"Punto 4: error importando Reserva ({type(exc).__name__}: {exc})."

    if not hasattr(modulo, "Reserva"):
        return "Punto 4: clase_reserva.py existe, pero no expone una clase Reserva."
    return "Punto 4: clase Reserva localizada e importada. Falta verificar su API y ciclo de vida con pruebas reales."


def main() -> None:
    registros = ejecutar_simulaciones()
    print("\nSOFTWARE FJ - SIMULACIONES DE INTEGRACION (PUNTOS 1, 2, 3 Y 5)")
    print("-" * 75)
    for caso in registros:
        estado = "OK" if caso.correcto else "FALLO"
        print(f"{caso.numero:02d}. [{estado}] {caso.nombre}: {caso.detalle}")

    buenos = sum(c.correcto for c in registros)
    print("-" * 75)
    print(f"Resultado: {buenos}/{len(registros)} simulaciones correctas.")
    print(verificar_reserva())
    print("Nota: esta verificacion parcial no sustituye las pruebas del punto 4.")
    if buenos != len(registros):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
