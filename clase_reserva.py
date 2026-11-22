"""Punto 4 - Software FJ: reservas de salas, equipos y asesorías.

Requiere clase_abstracta_general.py y clase_servicios.py en la misma carpeta.
La clase Cliente del compañero se conectará cuando esté disponible.
"""
from __future__ import annotations

from math import isfinite
from typing import Any

from clase_abstracta_general import (
    EntidadBase, configurar_logger, ErrorSoftwareFJ, ErrorValidacionDato,
    ErrorOperacionNoPermitida, ErrorServicioNoDisponible,
    ErrorCalculoInconsistente, ErrorReserva,
)
from clase_servicios import Servicio, AlquilerEquipo


class Reserva(EntidadBase):
    """Gestiona una reserva con estados y manejo seguro de excepciones.

    Estado inicial: PENDIENTE.
    Transiciones: PENDIENTE -> CONFIRMADA -> PROCESADA.
    Se permite cancelar PENDIENTE o CONFIRMADA, no PROCESADA.
    """

    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    PROCESADA = "PROCESADA"
    CANCELADA = "CANCELADA"

    def __init__(
        self,
        id_entidad: str,
        cliente: Any,
        servicio: Servicio,
        duracion: int,
        *,
        impuesto_pct: float = 0.0,
        descuento_pct: float = 0.0,
        cargo_adicional: float = 0.0,
        **parametros: Any,
    ) -> None:
        self._logger = configurar_logger()
        try:
            super().__init__(id_entidad)
            self._cliente = cliente
            self._servicio = servicio
            self._duracion = duracion
            self._impuesto_pct = impuesto_pct
            self._descuento_pct = descuento_pct
            self._cargo_adicional = cargo_adicional
            self._parametros = dict(parametros)
            self._estado = self.PENDIENTE
            self._total: float | None = None
            self._unidades_asignadas = 0
            self._validar_datos()
        except (ErrorSoftwareFJ, TypeError, ValueError) as exc:
            self._logger.error("Creación de reserva rechazada: %s", exc)
            raise
        else:
            self._logger.info("Creación de reserva %s: estado PENDIENTE", self.id_entidad)

    @property
    def cliente(self) -> Any:
        """Devuelve el objeto Cliente, sin copiar datos sensibles."""
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def duracion(self) -> int:
        return self._duracion

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def total(self) -> float | None:
        """El monto queda registrado al confirmar la reserva."""
        return self._total

    @staticmethod
    def _identificador_cliente(cliente: Any) -> str:
        """Admite id_entidad o id_cliente en el módulo Cliente aún pendiente."""
        if cliente is None or isinstance(cliente, (str, int, float, bool, dict)):
            raise ErrorValidacionDato("Debe suministrarse un objeto Cliente válido.")
        identificador = getattr(cliente, "id_entidad", None)
        if identificador is None:
            identificador = getattr(cliente, "id_cliente", None)
        if (not isinstance(identificador, (str, int))
                or isinstance(identificador, bool) or not str(identificador).strip()):
            raise ErrorValidacionDato("El cliente debe tener un id_entidad o id_cliente válido.")
        return str(identificador).strip()

    def _validar_cliente(self) -> str:
        id_cliente = self._identificador_cliente(self._cliente)
        # Algunas implementaciones usan 'activo'; otras, 'activa'.
        activo = getattr(self._cliente, "activo", None)
        if activo is None:
            activo = getattr(self._cliente, "activa", True)
        if activo is False:
            raise ErrorOperacionNoPermitida(f"El cliente {id_cliente} no está activo.")
        return id_cliente

    def _validar_datos(self) -> None:
        self._validar_cliente()
        if not isinstance(self._servicio, Servicio):
            raise ErrorValidacionDato("La reserva exige un objeto de tipo Servicio.")
        if not self._servicio.activa or not self._servicio.disponible:
            raise ErrorServicioNoDisponible("El servicio no se encuentra disponible.")
        if isinstance(self._duracion, bool) or not isinstance(self._duracion, int) or self._duracion <= 0:
            raise ErrorValidacionDato("La duración debe ser un número entero positivo.")
        for nombre, valor, minimo, maximo in (
            ("impuesto_pct", self._impuesto_pct, 0, 100),
            ("descuento_pct", self._descuento_pct, 0, 100),
            ("cargo_adicional", self._cargo_adicional, 0, None),
        ):
            if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not isfinite(valor):
                raise ErrorCalculoInconsistente(f"{nombre} debe ser un número finito.")
            if valor < minimo or (maximo is not None and valor > maximo):
                raise ErrorCalculoInconsistente(f"Valor fuera del rango permitido: {nombre}.")
        self._servicio.validar_parametros(self._duracion, **self._parametros)

    def calcular_total(self) -> float:
        """Calcula el valor según el servicio: polimorfismo y parámetros opcionales."""
        try:
            if self._estado == self.CANCELADA:
                raise ErrorOperacionNoPermitida("No se cotizan reservas canceladas.")
            if self._total is not None:
                return self._total
            self._validar_datos()
            total = self._servicio.calcular_costo(
                self._duracion,
                impuesto_pct=self._impuesto_pct,
                descuento_pct=self._descuento_pct,
                cargo_adicional=self._cargo_adicional,
                **self._parametros,
            )
            if not isfinite(total) or total < 0:
                raise ErrorCalculoInconsistente("El total de la reserva no es válido.")
            return total
        except ErrorSoftwareFJ as exc:
            self._logger.error("Reserva %s: error de cálculo: %s", self.id_entidad, exc)
            raise
        except Exception as exc:
            self._logger.exception("Reserva %s: error inesperado de cálculo", self.id_entidad)
            raise ErrorReserva("No fue posible calcular el importe de la reserva.") from exc

    def confirmar(self) -> float:
        """Confirma y, en alquiler de equipos, descuenta stock una sola vez."""
        if self._estado != self.PENDIENTE:
            error = ErrorOperacionNoPermitida("Solo se pueden confirmar reservas pendientes.")
            self._logger.warning("Reserva %s: %s", self.id_entidad, error)
            raise error
        try:
            total = self.calcular_total()
            if isinstance(self._servicio, AlquilerEquipo):
                cantidad = self._parametros.get("cantidad", 1)
                self._servicio.consumir_unidades(cantidad)
                self._unidades_asignadas = cantidad
            self._total = total
            self._estado = self.CONFIRMADA
        except ErrorSoftwareFJ as exc:
            self._logger.error("No se confirmó la reserva %s: %s", self.id_entidad, exc)
            raise
        except Exception as exc:
            self._logger.exception("Error inesperado al confirmar %s", self.id_entidad)
            raise ErrorReserva("Fallo inesperado al confirmar la reserva.") from exc
        else:
            self._logger.info("Reserva %s CONFIRMADA; total: %.2f", self.id_entidad, total)
            return total
        finally:
            self._logger.info("Fin del intento de confirmación de %s", self.id_entidad)

    def procesar(self) -> None:
        """Marca el servicio como procesado únicamente si fue confirmado."""
        if self._estado != self.CONFIRMADA:
            self._logger.warning("Procesamiento denegado para %s, estado %s", self.id_entidad, self._estado)
            raise ErrorOperacionNoPermitida("Solo se procesan reservas confirmadas.")
        self._estado = self.PROCESADA
        self._logger.info("Reserva %s PROCESADA", self.id_entidad)

    def cancelar(self) -> None:
        """Cancela una reserva no procesada y devuelve unidades bloqueadas."""
        if self._estado not in (self.PENDIENTE, self.CONFIRMADA):
            self._logger.warning("Cancelación denegada de %s, estado %s", self.id_entidad, self._estado)
            raise ErrorOperacionNoPermitida("Una reserva procesada o cancelada no se puede cancelar.")
        try:
            if isinstance(self._servicio, AlquilerEquipo) and self._unidades_asignadas:
                self._servicio.devolver_unidades(self._unidades_asignadas)
                self._unidades_asignadas = 0
            self._estado = self.CANCELADA
            self._logger.info("Reserva %s CANCELADA", self.id_entidad)
        except ErrorSoftwareFJ as exc:
            self._logger.error("No se canceló la reserva %s: %s", self.id_entidad, exc)
            raise
        except Exception as exc:
            self._logger.exception("Error inesperado al cancelar %s", self.id_entidad)
            raise ErrorReserva("No fue posible cancelar la reserva.") from exc

    def resumen(self) -> str:
        return (
            f"Reserva {self.id_entidad} | Cliente: {self._identificador_cliente(self._cliente)} | "
            f"Servicio: {self._servicio.nombre} | Duración: {self._duracion} | "
            f"Estado: {self._estado} | Total: {self._total if self._total is not None else 'Pendiente'}"
        )
