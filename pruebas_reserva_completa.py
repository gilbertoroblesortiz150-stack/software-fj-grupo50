"""Software FJ: pruebas del Punto 4 con los demas componentes del proyecto.

Ejecutar desde la carpeta del repositorio:
    py pruebas_reserva_completa.py

Las pruebas muestran exitos y errores esperados. Un error esperado cuenta como
correcto solo cuando el programa lo rechaza mediante la excepcion adecuada.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from clase_abstracta_general import (
    EntidadBase, ErrorCalculoInconsistente, ErrorOperacionNoPermitida,
    ErrorServicioNoDisponible, ErrorValidacionDato,
)
from clase_cliente import Cliente
from clase_servicios import ReservaSala, AlquilerEquipo, AsesoriaEspecializada
from clase_reserva import Reserva
from calculador_costos import CalculadorCostos


@dataclass
class Resultado:
    numero: int
    nombre: str
    correcto: bool
    detalle: str


def debe_rechazar(accion: Callable[[], object], tipo: type[Exception]) -> str:
    """Una operacion invalida debe generar la excepcion prevista."""
    try:
        accion()
    except tipo as exc:
        return f"Rechazo correcto: {type(exc).__name__}"
    except Exception as exc:
        raise AssertionError(f"Se esperaba {tipo.__name__}, ocurrio {type(exc).__name__}: {exc}") from exc
    raise AssertionError(f"Se esperaba {tipo.__name__}, pero la operacion fue aceptada")


def ejecutar() -> list[Resultado]:
    resultados: list[Resultado] = []
    cliente = Cliente('C-001', 'Felipe Jimenez', 'felipe@example.com',
                      '3001234567', '1090456789', 'clave123')
    sala = ReservaSala('S-001', 'Sala de reuniones', 70000, capacidad_maxima=10)
    equipo = AlquilerEquipo('E-001', 'Proyector', 40000, unidades_disponibles=2)
    asesoria = AsesoriaEspecializada('A-001', 'Asesoria Python', 120000, 'Programacion')
    coto = CalculadorCostos()
    datos: dict[str, Reserva] = {}

    def probar(nombre: str, accion: Callable[[], object]) -> None:
        numero = len(resultados) + 1
        try:
            detalle = accion()
        except Exception as exc:
            resultados.append(Resultado(numero,nombre,False,f'{type(exc).__name__}: {exc}'))
        else:
            resultados.append(Resultado(numero,nombre,True,str(detalle or 'Verificado')))

    def crear_reserva_sala():
        r = Reserva('R-001', cliente, sala, 3, impuesto_pct=19, descuento_pct=10, asistentes=6)
        assert isinstance(r, EntidadBase)
        assert r.estado == Reserva.PENDIENTE and r.total is None
        assert r.cliente is cliente and r.servicio is sala
        datos['sala'] = r
        return f'Estado inicial: {r.estado}'

    def cotizar_sala():
        r=datos['sala']
        total=r.calcular_total()
        assert total == 224910.0, total
        assert r.estado == Reserva.PENDIENTE
        return f'Cotizacion antes de confirmar: ${total:,.2f}'

    def confirmar_sala():
        r=datos['sala']
        total=r.confirmar()
        assert total == 224910.0 and r.total == total and r.estado == Reserva.CONFIRMADA
        return f'Estado {r.estado}; total ${total:,.2f}'

    def confirmar_dos_veces():
        return debe_rechazar(datos['sala'].confirmar,ErrorOperacionNoPermitida)

    def procesar_sala():
        r=datos['sala']; r.procesar()
        assert r.estado == Reserva.PROCESADA
        return f'Estado {r.estado}'

    def cancelar_procesada():
        return debe_rechazar(datos['sala'].cancelar,ErrorOperacionNoPermitida)

    def procesar_pendiente():
        r=Reserva('R-002', cliente, sala, 1)
        return debe_rechazar(r.procesar,ErrorOperacionNoPermitida)

    def cancelar_pendiente():
        r=Reserva('R-003', cliente, sala, 1)
        r.cancelar()
        assert r.estado == Reserva.CANCELADA
        datos['cancelada'] = r
        return f'Estado {r.estado}'

    def confirmar_cancelada():
        return debe_rechazar(datos['cancelada'].confirmar,ErrorOperacionNoPermitida)

    def rechazar_duracion_cero():
        return debe_rechazar(lambda: Reserva('R-004',cliente,sala,0),ErrorValidacionDato)

    def rechazar_cliente_inactivo():
        otro=Cliente('C-002','Ana Lopez','ana@example.com','3001234568','1090456788','claveABC')
        otro.desactivar()
        return debe_rechazar(lambda: Reserva('R-005',otro,sala,1),ErrorOperacionNoPermitida)

    def rechazar_servicio_no_disponible():
        otra_sala=ReservaSala('S-002','Sala cerrada',30000,5,disponible=False)
        return debe_rechazar(lambda: Reserva('R-006',cliente,otra_sala,1),ErrorServicioNoDisponible)

    def rechazar_aforo():
        return debe_rechazar(lambda: Reserva('R-007',cliente,sala,1,asistentes=15),ErrorOperacionNoPermitida)

    def descontar_stock_equipo():
        r=Reserva('R-008',cliente,equipo,2,cantidad=2)
        assert equipo.unidades_disponibles == 2
        assert r.confirmar() == 160000.0
        assert equipo.unidades_disponibles == 0 and not equipo.disponible
        datos['equipo']=r
        return 'Reserva confirmada: stock 2 -> 0'

    def rechazar_sin_stock():
        return debe_rechazar(lambda: Reserva('R-009',cliente,equipo,1,cantidad=1),ErrorServicioNoDisponible)

    def cancelar_y_devolver_stock():
        r=datos['equipo']; r.cancelar()
        assert r.estado == Reserva.CANCELADA
        assert equipo.unidades_disponibles == 2 and equipo.disponible
        return 'Reserva cancelada: stock 0 -> 2; servicio disponible'

    def rechazar_segunda_cancelacion():
        return debe_rechazar(datos['equipo'].cancelar,ErrorOperacionNoPermitida)

    def confirmar_asesoria():
        r=Reserva('R-010',cliente,asesoria,2,impuesto_pct=19)
        assert r.confirmar() == 285600.0
        r.procesar()
        assert r.estado == Reserva.PROCESADA
        return 'Asesoria: confirmada y procesada; total $285,600.00'

    def rechazar_descuento_negativo():
        return debe_rechazar(lambda: Reserva('R-011',cliente,sala,1,descuento_pct=-5),ErrorCalculoInconsistente)

    def comprobar_precio_con_calculador():
        r=Reserva('R-012',cliente,sala,2,impuesto_pct=19)
        assert r.calcular_total() == coto.calcular(70000,duracion=2,impuesto_pct=19)
        return 'Reserva y CalculadorCostos coinciden en $166,600.00'

    def rechazar_cliente_incorrecto():
        return debe_rechazar(lambda: Reserva('R-013','C-001',sala,1),ErrorValidacionDato)

    escenarios = [
        ('Crear reserva de sala',crear_reserva_sala),
        ('Cotizar sala con impuesto y descuento',cotizar_sala),
        ('Confirmar reserva de sala',confirmar_sala),
        ('Rechazar doble confirmacion',confirmar_dos_veces),
        ('Procesar reserva confirmada',procesar_sala),
        ('Rechazar cancelacion de procesada',cancelar_procesada),
        ('Rechazar procesamiento de pendiente',procesar_pendiente),
        ('Cancelar reserva pendiente',cancelar_pendiente),
        ('Rechazar confirmacion de cancelada',confirmar_cancelada),
        ('Rechazar duracion cero',rechazar_duracion_cero),
        ('Rechazar cliente inactivo',rechazar_cliente_inactivo),
        ('Rechazar servicio no disponible',rechazar_servicio_no_disponible),
        ('Rechazar exceso de aforo',rechazar_aforo),
        ('Descontar inventario al confirmar equipo',descontar_stock_equipo),
        ('Rechazar reserva sin inventario',rechazar_sin_stock),
        ('Devolver inventario al cancelar equipo',cancelar_y_devolver_stock),
        ('Rechazar doble cancelacion',rechazar_segunda_cancelacion),
        ('Confirmar y procesar asesoria',confirmar_asesoria),
        ('Rechazar descuento negativo',rechazar_descuento_negativo),
        ('Comparar tarifa con calculador de costos',comprobar_precio_con_calculador),
        ('Rechazar cliente de tipo incorrecto',rechazar_cliente_incorrecto),
    ]
    for nombre,accion in escenarios:
        probar(nombre,accion)
    return resultados


def main() -> None:
    print('\nSOFTWARE FJ - PRUEBAS DE RESERVA E INTEGRACION TOTAL')
    print('-'*74)
    resultados=ejecutar()
    for r in resultados:
        print(f'{r.numero:02d}. [{"OK" if r.correcto else "FALLO"}] {r.nombre}: {r.detalle}')
    exitos=sum(r.correcto for r in resultados)
    print('-'*74)
    print(f'Resultado: {exitos}/{len(resultados)} simulaciones correctas.')
    if exitos != len(resultados):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
