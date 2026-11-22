"""Punto 3 - Servicios del sistema Software FJ.

Importa la clase abstracta y las excepciones compartidas del punto 1.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import Any

from clase_abstracta_general import (
    EntidadBase,
    ErrorSoftwareFJ,
    ErrorValidacionDato,
    ErrorOperacionNoPermitida,
    ErrorServicioNoDisponible,
    ErrorCalculoInconsistente,
)


# ==============================================================================
# PUNTO 3: CLASE ABSTRACTA SERVICIO
# ==============================================================================
class Servicio(EntidadBase, ABC):
    """Clase abstracta que representa los servicios ofrecidos por Software FJ."""

    def __init__(
        self,
        id_entidad: str,
        nombre: str,
        tarifa_unitaria: float,
        disponible: bool = True,
    ) -> None:
        # Llama al constructor de EntidadBase para validar y asignar id_entidad
        super().__init__(id_entidad)
        # Valida que el nombre del servicio sea un string no vacío
        if not isinstance(nombre, str) or not nombre.strip():
            # Rechaza nombres vacíos o de tipo incorrecto
            raise ErrorValidacionDato("El nombre del servicio no puede estar vacío.")
        # Valida que la tarifa unitaria sea numérica y estrictamente mayor a cero
        if not isinstance(tarifa_unitaria, (int, float)) or tarifa_unitaria <= 0:
            # Evita tarifas negativas o en cero que distorsionarían cobros
            raise ErrorCalculoInconsistente(
                f"La tarifa unitaria del servicio '{nombre}' debe ser mayor que cero."
            )
        # Guarda el nombre limpio del servicio
        self._nombre: str = nombre.strip()
        # Convierte y guarda la tarifa base como flotante
        self._tarifa_unitaria: float = float(tarifa_unitaria)
        # Guarda el estado de disponibilidad del servicio (True/False)
        self._disponible: bool = bool(disponible)

    @property
    def nombre(self) -> str:
        """Devuelve el nombre del servicio."""
        # Expone de forma controlada el nombre del servicio
        return self._nombre

    @property
    def tarifa_unitaria(self) -> float:
        """Devuelve la tarifa unitaria base del servicio."""
        # Expone la tarifa unitaria configurada
        return self._tarifa_unitaria

    @property
    def disponible(self) -> bool:
        """Indica si el servicio está disponible para ser reservado."""
        # Retorna el estado booleano de disponibilidad
        return self._disponible

    def cambiar_disponibilidad(self, estado: bool) -> None:
        """Actualiza de forma segura la disponibilidad del servicio."""
        # Verifica que el nuevo estado sea booleano
        if not isinstance(estado, bool):
            # Lanza error de validación si no se pasa un booleano
            raise ErrorValidacionDato("El estado de disponibilidad debe ser True o False.")
        # Actualiza el atributo protegido _disponible
        self._disponible = estado

    @abstractmethod
    def validar_parametros(self, duracion: int, **kwargs: Any) -> None:
        """Valida duración y parámetros específicos de cada tipo de servicio."""

    @abstractmethod
    def calcular_costo_base(self, duracion: int, **kwargs: Any) -> float:
        """Calcula el costo base (antes de descuentos e impuestos) del servicio."""

    @abstractmethod
    def describir(self) -> str:
        """Devuelve una descripción detallada del servicio."""

    def calcular_costo(
        self,
        duracion: int,
        impuesto_pct: float = 0.0,
        descuento_pct: float = 0.0,
        cargo_adicional: float = 0.0,
        **kwargs: Any,
    ) -> float:
        """Calcula el costo final aplicando parámetros opcionales de descuento, cargo e impuesto."""
        # Valida que el porcentaje de impuesto esté dentro del rango [0, 100]
        if not isinstance(impuesto_pct, (int, float)) or not (0.0 <= impuesto_pct <= 100.0):
            # Lanza error si el impuesto está fuera de rango o no es numérico
            raise ErrorCalculoInconsistente("El porcentaje de impuesto debe estar entre 0 y 100.")
        # Valida que el porcentaje de descuento esté dentro del rango [0, 100]
        if not isinstance(descuento_pct, (int, float)) or not (0.0 <= descuento_pct <= 100.0):
            # Lanza error si el descuento está fuera de rango o no es numérico
            raise ErrorCalculoInconsistente("El porcentaje de descuento debe estar entre 0 y 100.")
        # Valida que el cargo adicional no sea negativo
        if not isinstance(cargo_adicional, (int, float)) or cargo_adicional < 0:
            # Impide cargos adicionales negativos
            raise ErrorCalculoInconsistente("El cargo adicional no puede ser negativo.")

        # Inicia bloque try para ejecutar validaciones y cálculos de forma segura
        try:
            # Ejecuta la validación específica de la subclase (sala, equipo o asesoría)
            self.validar_parametros(duracion, **kwargs)
            # Calcula el subtotal sumando el costo base polimórfico y el cargo adicional
            subtotal = self.calcular_costo_base(duracion, **kwargs) + float(cargo_adicional)
            # Verifica que el subtotal no sea negativo
            if subtotal < 0:
                # Lanza error si el subtotal resulta inconsistente
                raise ErrorCalculoInconsistente("El subtotal calculado resultó negativo.")

            # Aplica el porcentaje de descuento sobre el subtotal
            con_descuento = subtotal * (1.0 - (float(descuento_pct) / 100.0))
            # Aplica el porcentaje de impuesto sobre el monto con descuento
            total_final = con_descuento * (1.0 + (float(impuesto_pct) / 100.0))

            # Verifica que el total final no sea negativo
            if total_final < 0:
                # Lanza error si el cálculo final arroja un valor negativo
                raise ErrorCalculoInconsistente("El costo final calculado resultó negativo.")

            # Redondea el resultado a dos decimales y lo retorna
            return round(total_final, 2)
        # Re-lanza sin alterar las excepciones propias del dominio
        except ErrorSoftwareFJ:
            # Propaga la excepción original del dominio
            raise
        # Captura cualquier otra excepción inesperada y la encadena con 'from exc'
        except Exception as exc:
            # Encadena la excepción original para conservar la traza de causa raíz
            raise ErrorCalculoInconsistente(
                f"Error inesperado al calcular el costo de '{self._nombre}'."
            ) from exc

    def resumen(self) -> str:
        """Implementa resumen() de EntidadBase con el estado actual del servicio."""
        # Define texto legible según disponibilidad
        estado_txt = "Disponible" if self._disponible else "No disponible"
        # Retorna cadena resumen con ID, nombre y disponibilidad
        return f"[Servicio {self._id_entidad}] {self._nombre} - {estado_txt}"


# ==============================================================================
# SUBCLASE 1: RESERVA DE SALAS
# ==============================================================================
class ReservaSala(Servicio):
    """Servicio especializado para reservar salas (duración medida en horas)."""

    def __init__(
        self,
        id_entidad: str,
        nombre: str,
        tarifa_hora: float,
        capacidad_maxima: int,
        disponible: bool = True,
    ) -> None:
        # Inicializa atributos comunes mediante la clase padre Servicio
        super().__init__(id_entidad, nombre, tarifa_hora, disponible)
        # Verifica que la capacidad máxima sea un entero positivo
        if not isinstance(capacidad_maxima, int) or capacidad_maxima <= 0:
            # Lanza error si la capacidad es inválida
            raise ErrorValidacionDato("La capacidad máxima de la sala debe ser mayor que cero.")
        # Almacena la capacidad máxima de personas de la sala
        self._capacidad_maxima: int = capacidad_maxima

    @property
    def capacidad_maxima(self) -> int:
        """Devuelve la capacidad máxima de asistentes de la sala."""
        # Retorna el límite de personas permitido
        return self._capacidad_maxima

    def validar_parametros(self, duracion: int, **kwargs: Any) -> None:
        """Valida horas de reserva y número opcional de asistentes."""
        # Verifica que la duración en horas sea un entero positivo
        if not isinstance(duracion, int) or duracion <= 0:
            # Rechaza duraciones menores o iguales a cero o no enteras
            raise ErrorValidacionDato("La duración de la reserva de sala debe ser de al menos 1 hora.")
        # Obtiene el parámetro opcional 'asistentes' desde kwargs
        asistentes = kwargs.get("asistentes")
        # Si se indicó cantidad de asistentes, valida tipo, valor y aforo
        if asistentes is not None:
            # Verifica que 'asistentes' sea un entero positivo
            if not isinstance(asistentes, int) or asistentes <= 0:
                # Lanza error si la cantidad de asistentes no es válida
                raise ErrorValidacionDato("El número de asistentes debe ser mayor que cero.")
            # Verifica que no exceda la capacidad máxima de la sala
            if asistentes > self._capacidad_maxima:
                # Impide reservar por encima del aforo permitido
                raise ErrorOperacionNoPermitida(
                    f"Los asistentes ({asistentes}) exceden la capacidad de '{self._nombre}' ({self._capacidad_maxima})."
                )

    def calcular_costo_base(self, duracion: int, **kwargs: Any) -> float:
        """Calcula el costo base multiplicando tarifa por hora por cantidad de horas."""
        # Multiplica la tarifa por hora por la duración en horas
        return self._tarifa_unitaria * duracion

    def describir(self) -> str:
        """Describe la sala, su aforo y su tarifa por hora."""
        # Retorna descripción formateada del servicio de sala
        return (
            f"Sala '{self._nombre}' | Capacidad máx.: {self._capacidad_maxima} personas | "
            f"Tarifa/hora: ${self._tarifa_unitaria:,.2f}"
        )


# ==============================================================================
# SUBCLASE 2: ALQUILER DE EQUIPOS
# ==============================================================================
class AlquilerEquipo(Servicio):
    """Servicio especializado para alquilar equipos (duración medida en días)."""

    def __init__(
        self,
        id_entidad: str,
        nombre: str,
        tarifa_dia: float,
        unidades_disponibles: int,
        disponible: bool = True,
    ) -> None:
        # Inicializa atributos generales en Servicio
        super().__init__(id_entidad, nombre, tarifa_dia, disponible)
        # Valida que las unidades iniciales no sean negativas
        if not isinstance(unidades_disponibles, int) or unidades_disponibles < 0:
            # Lanza error si el inventario inicial es negativo o no entero
            raise ErrorValidacionDato("Las unidades disponibles deben ser un entero mayor o igual a 0.")
        # Guarda el inventario disponible del equipo
        self._unidades_disponibles: int = unidades_disponibles
        # Si arranca con 0 unidades, marca el servicio como no disponible
        if self._unidades_disponibles == 0:
            # Actualiza disponibilidad a False cuando no hay stock
            self._disponible = False

    @property
    def unidades_disponibles(self) -> int:
        """Devuelve la cantidad de unidades disponibles en inventario."""
        # Retorna el número actual de unidades
        return self._unidades_disponibles

    def consumir_unidades(self, cantidad: int) -> None:
        """Descuenta unidades alquiladas si hay disponibilidad suficiente."""
        # Valida que la cantidad a descontar sea un entero positivo
        if not isinstance(cantidad, int) or cantidad <= 0:
            # Lanza error si se solicita descontar 0 o menos unidades
            raise ErrorValidacionDato("La cantidad de unidades a consumir debe ser mayor que cero.")
        # Comprueba que haya suficiente stock para atender la solicitud
        if cantidad > self._unidades_disponibles:
            # Lanza error de servicio no disponible por falta de unidades
            raise ErrorServicioNoDisponible(
                f"Stock insuficiente en '{self._nombre}': solicitadas {cantidad}, disponibles {self._unidades_disponibles}."
            )
        # Resta las unidades asignadas al inventario
        self._unidades_disponibles -= cantidad
        # Si el stock llega a cero, desactiva la disponibilidad del servicio
        if self._unidades_disponibles == 0:
            # Marca el servicio como no disponible
            self._disponible = False

    def devolver_unidades(self, cantidad: int) -> None:
        """Restituye unidades al inventario cuando una reserva es cancelada."""
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise ErrorValidacionDato("La cantidad de unidades a devolver debe ser un entero positivo.")
        sin_stock = self._unidades_disponibles == 0
        self._unidades_disponibles += cantidad
        # Si el servicio se agotó automáticamente, vuelve a estar disponible.
        # No cambia una desactivación manual cuando aún existía inventario.
        if sin_stock and self._activa:
            self._disponible = True

    def validar_parametros(self, duracion: int, **kwargs: Any) -> None:
        """Valida días de alquiler y cantidad de unidades solicitadas."""
        # Verifica que la duración en días sea un entero positivo
        if not isinstance(duracion, int) or duracion <= 0:
            # Lanza error si la duración en días es inválida
            raise ErrorValidacionDato("La duración del alquiler debe ser de al menos 1 día.")
        # Obtiene la cantidad de equipos solicitados (por defecto 1 unidad)
        cantidad = kwargs.get("cantidad", 1)
        # Valida que cantidad sea un entero positivo
        if not isinstance(cantidad, int) or cantidad <= 0:
            # Rechaza cantidades no positivas
            raise ErrorValidacionDato("La cantidad de equipos debe ser mayor que cero.")
        # Valida que exista stock suficiente para la cantidad pedida
        if cantidad > self._unidades_disponibles:
            # Lanza error si no hay suficientes unidades disponibles
            raise ErrorServicioNoDisponible(
                f"No hay {cantidad} unidades de '{self._nombre}' disponibles (stock: {self._unidades_disponibles})."
            )

    def calcular_costo_base(self, duracion: int, **kwargs: Any) -> float:
        """Calcula el costo base según tarifa diaria, días y cantidad de unidades."""
        # Obtiene la cantidad de unidades a cotizar (por defecto 1)
        cantidad = kwargs.get("cantidad", 1)
        # Calcula tarifa diaria * días * cantidad de equipos
        return self._tarifa_unitaria * duracion * cantidad

    def describir(self) -> str:
        """Describe el equipo, unidades disponibles y tarifa diaria."""
        # Retorna descripción formateada del equipo
        return (
            f"Equipo '{self._nombre}' | Disponibles: {self._unidades_disponibles} und. | "
            f"Tarifa/día: ${self._tarifa_unitaria:,.2f}"
        )


# ==============================================================================
# SUBCLASE 3: ASESORÍAS ESPECIALIZADAS
# ==============================================================================
class AsesoriaEspecializada(Servicio):
    """Servicio especializado para asesorías técnicas (duración medida en horas)."""

    def __init__(
        self,
        id_entidad: str,
        nombre: str,
        tarifa_hora: float,
        especialidad: str,
        disponible: bool = True,
    ) -> None:
        # Inicializa atributos comunes en Servicio
        super().__init__(id_entidad, nombre, tarifa_hora, disponible)
        # Verifica que el área de especialidad sea un texto no vacío
        if not isinstance(especialidad, str) or not especialidad.strip():
            # Lanza error si no se especifica el área de asesoría
            raise ErrorValidacionDato("La especialidad de la asesoría no puede estar vacía.")
        # Guarda la especialidad limpia
        self._especialidad: str = especialidad.strip()

    @property
    def especialidad(self) -> str:
        """Devuelve el área de especialidad de la asesoría."""
        # Retorna el nombre de la especialidad
        return self._especialidad

    def validar_parametros(self, duracion: int, **kwargs: Any) -> None:
        """Valida que la duración de la asesoría sea de al menos 1 hora."""
        # Verifica que la duración en horas sea un entero positivo
        if not isinstance(duracion, int) or duracion <= 0:
            # Rechaza duraciones menores a 1 hora o no enteras
            raise ErrorValidacionDato("La duración de la asesoría debe ser de al menos 1 hora.")

    def calcular_costo_base(self, duracion: int, **kwargs: Any) -> float:
        """Calcula el costo base multiplicando tarifa por hora por duración."""
        # Retorna el costo base por horas de asesoría
        return self._tarifa_unitaria * duracion

    def describir(self) -> str:
        """Describe la asesoría, su especialidad y tarifa por hora."""
        # Retorna descripción formateada de la asesoría
        return (
            f"Asesoría '{self._nombre}' | Especialidad: {self._especialidad} | "
            f"Tarifa/hora: ${self._tarifa_unitaria:,.2f}"
        )


# ==============================================================================
# EJECUCIÓN SECUENCIAL DE PRUEBAS PARA EL PUNTO 3
# ==============================================================================
def probar_servicios_secuencialmente() -> None:
    """Ejecuta pruebas paso a paso y registra resultados en prueba_servicios.log."""
    # Configura logger de prueba para validar registro sin fallos
    log_prueba = logging.getLogger("PruebaServicios")
    log_prueba.setLevel(logging.INFO)
    if not log_prueba.handlers:
        handler = logging.FileHandler("prueba_servicios.log", mode="a", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        log_prueba.addHandler(handler)

    print("--- Paso 1: Crear instancias válidas de los 3 servicios ---")
    # Crea una sala con capacidad de 10 personas a $70,000/hora
    sala = ReservaSala("SALA-01", "Sala Conferencias A", 70000.0, capacidad_maxima=10)
    # Crea un alquiler de portátiles con 4 unidades a $40,000/día
    equipo = AlquilerEquipo("EQ-01", "Portátil Ingeniería", 40000.0, unidades_disponibles=4)
    # Crea una asesoría en ciberseguridad a $120,000/hora
    asesoria = AsesoriaEspecializada("ASE-01", "Auditoría OWASP", 120000.0, "Ciberseguridad")
    # Agrupa los tres servicios para probar polimorfismo
    servicios = [sala, equipo, asesoria]
    for srv in servicios:
        print(" ", srv.describir())
        log_prueba.info("Creado: %s", srv.resumen())

    print("\n--- Paso 2: Calcular costos con descuento, cargo e impuesto ---")
    # Calcula costo de sala por 3 horas, 10% descuento y 19% IVA con 6 asistentes
    total_sala = sala.calcular_costo(duracion=3, impuesto_pct=19.0, descuento_pct=10.0, asistentes=6)
    print(f"  Total Sala (3h, desc 10%, IVA 19%): ${total_sala:,.2f}")
    # Calcula costo de equipo por 2 días y 2 unidades con 5% descuento y 19% IVA
    total_equipo = equipo.calcular_costo(duracion=2, impuesto_pct=19.0, descuento_pct=5.0, cantidad=2)
    print(f"  Total Equipo (2d x 2 und, desc 5%, IVA 19%): ${total_equipo:,.2f}")
    # Calcula costo de asesoría por 4 horas sin descuento y con 19% IVA
    total_asesoria = asesoria.calcular_costo(duracion=4, impuesto_pct=19.0)
    print(f"  Total Asesoría (4h, IVA 19%): ${total_asesoria:,.2f}")

    print("\n--- Paso 3: Consumir unidades de equipo y validar límite ---")
    # Consume 3 de las 4 unidades disponibles
    equipo.consumir_unidades(3)
    print(f"  Unidades restantes tras alquilar 3: {equipo.unidades_disponibles}")
    try:
        # Intenta alquilar 2 unidades cuando solo queda 1
        equipo.calcular_costo(duracion=1, cantidad=2)
    except ErrorServicioNoDisponible as exc:
        # Registra el error esperado sin detener la ejecución
        print(f"  Error esperado capturado: {exc}")
        log_prueba.error("Falta de stock detectada: %s", exc)

    print("\n--- Paso 4: Validar aforo de sala y encadenamiento de excepciones ---")
    try:
        # Intenta meter 15 personas en una sala de capacidad 10
        sala.calcular_costo(duracion=2, asistentes=15)
    except ErrorOperacionNoPermitida as exc:
        print(f"  Error de aforo capturado: {exc}")
        log_prueba.error("Aforo excedido: %s", exc)

    try:
        # Provoca un error interno forzando una operación inválida dentro de un bloque anidado
        try:
            _ = float("no_es_numero")
        except ValueError as causa:
            raise ErrorCalculoInconsistente("Fallo al convertir tarifa externa") from causa
    except ErrorCalculoInconsistente as exc_encadenada:
        print(f"  Excepción encadenada: {exc_encadenada} -> Causa: {exc_encadenada.__cause__}")
        log_prueba.error("Excepción encadenada: %s (Causa: %s)", exc_encadenada, exc_encadenada.__cause__)

    print("\nPruebas del punto 3 completadas correctamente.")


if __name__ == "__main__":
    probar_servicios_secuencialmente()