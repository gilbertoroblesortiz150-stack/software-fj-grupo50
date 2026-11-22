from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any, Dict


# ==============================================================================
# CONFIGURACIÓN DE LOGS PARA EVENTOS Y ERRORES DEL SISTEMA
# ==============================================================================
def configurar_logger(
    nombre_archivo: str = "software_fj.log",
    nombre_logger: str = "SoftwareFJLogger",
) -> logging.Logger:
    """Configura y devuelve un logger que guarda eventos y errores en archivo."""
    # Obtiene o crea la instancia del logger identificada por nombre_logger
    logger = logging.getLogger(nombre_logger)
    # Establece el nivel mínimo de registro en INFO para capturar eventos y errores
    logger.setLevel(logging.INFO)

    # Evita agregar manejadores duplicados si la función se llama más de una vez
    if not logger.handlers:
        # Define el formato de cada línea del archivo de registro
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # Crea un manejador de archivo en modo 'a' (agregar) con codificación UTF-8
        manejador_archivo = logging.FileHandler(nombre_archivo, mode="a", encoding="utf-8")
        # Asocia el formato definido al manejador de archivo
        manejador_archivo.setFormatter(formato)
        # Registra el manejador en el logger
        logger.addHandler(manejador_archivo)

    # Retorna el logger listo para usarse en el sistema
    return logger


# ==============================================================================
# EXCEPCIONES PERSONALIZADAS COMPARTIDAS POR EL SISTEMA
# ==============================================================================
class ErrorSoftwareFJ(Exception):
    """Excepción base para todos los errores controlados de Software FJ."""


class ErrorValidacionDato(ErrorSoftwareFJ):
    """Se lanza cuando un dato o parámetro no cumple con las reglas de validación."""


class ErrorOperacionNoPermitida(ErrorSoftwareFJ):
    """Se lanza cuando una operación no es válida por reglas de negocio o estado."""


class ErrorServicioNoDisponible(ErrorSoftwareFJ):
    """Se lanza cuando un servicio está inactivo o sin capacidad/stock disponible."""


class ErrorCalculoInconsistente(ErrorSoftwareFJ):
    """Se lanza cuando ocurre un error numérico o un cálculo resulta inválido."""


class ErrorReserva(ErrorSoftwareFJ):
    """Se lanza cuando falla la creación, confirmación, procesamiento o cancelación de una reserva."""


# ==============================================================================
# PUNTO 1: CLASE ABSTRACTA GENERAL (ESTRUCTURA BASE DEL SISTEMA)
# ==============================================================================
class EntidadBase(ABC):
    """Clase abstracta general que define la estructura base de las entidades."""

    def __init__(self, id_entidad: str) -> None:
        # Valida que el identificador sea una cadena de texto no vacía
        if not isinstance(id_entidad, str) or not id_entidad.strip():
            # Lanza excepción de validación si el ID es inválido o está vacío
            raise ErrorValidacionDato("El ID de la entidad debe ser un texto no vacío.")
        # Normaliza el identificador quitando espacios extremos y pasando a mayúsculas
        self._id_entidad: str = id_entidad.strip().upper()
        # Registra la fecha y hora exacta de creación de la entidad
        self._fecha_creacion: datetime = datetime.now()
        # Indica si la entidad está activa dentro del sistema
        self._activa: bool = True

    @property
    def id_entidad(self) -> str:
        """Devuelve el identificador único de la entidad."""
        # Retorna el atributo protegido _id_entidad
        return self._id_entidad

    @property
    def fecha_creacion(self) -> datetime:
        """Devuelve la fecha y hora en que se creó la entidad."""
        # Retorna el objeto datetime de creación
        return self._fecha_creacion

    @property
    def activa(self) -> bool:
        """Indica si la entidad se encuentra activa."""
        # Retorna el estado booleano _activa
        return self._activa

    def desactivar(self) -> None:
        """Marca la entidad como inactiva de forma controlada."""
        # Verifica que la entidad no esté ya desactivada
        if not self._activa:
            # Lanza error si se intenta desactivar una entidad ya inactiva
            raise ErrorOperacionNoPermitida(
                f"La entidad '{self._id_entidad}' ya se encuentra inactiva."
            )
        # Cambia el estado a False
        self._activa = False

    def activar(self) -> None:
        """Reactiva la entidad si estaba inactiva."""
        # Cambia el estado a True
        self._activa = True

    def metadatos_base(self) -> Dict[str, Any]:
        """Devuelve un diccionario con los datos estructurales comunes de la entidad."""
        # Construye y retorna un diccionario con los atributos base
        return {
            "id_entidad": self._id_entidad,
            "fecha_creacion": self._fecha_creacion.isoformat(timespec="seconds"),
            "activa": self._activa,
            "tipo_clase": self.__class__.__name__,
        }

    @abstractmethod
    def resumen(self) -> str:
        """Método abstracto que obliga a cada clase derivada a entregar su resumen."""

    def __str__(self) -> str:
        """Representación legible por defecto apoyada en resumen()."""
        # Delega la representación en texto al método abstracto resumen()
        return self.resumen()


# ==============================================================================
# EJECUCIÓN SECUENCIAL DE PRUEBAS PARA EL PUNTO 1
# ==============================================================================
def probar_entidad_base_secuencialmente() -> None:
    """Ejecuta pruebas paso a paso de la estructura base y el registro de logs."""
    # Configura el logger de prueba para verificar escritura en archivo
    logger_prueba = configurar_logger(
        nombre_archivo="prueba_entidad_base.log",
        nombre_logger="PruebaEntidadBaseLogger",
    )

    print("--- Paso 1: Verificar que EntidadBase no se puede instanciar directamente ---")
    # Usa try/except/else/finally para validar el comportamiento abstracto
    try:
        # Intenta instanciar directamente la clase abstracta (debe fallar con TypeError)
        _ = EntidadBase("ENT-01")  # type: ignore[abstract]
    except TypeError as exc:
        # Registra el error esperado en consola y en el log
        print(f"  Comportamiento abstracto validado: {exc}")
        logger_prueba.info("Verificada restricción de clase abstracta EntidadBase: %s", exc)
    else:
        # Si llegara aquí, algo falló en la abstracción
        print("  Error inesperado: EntidadBase no debería instanciarse directamente.")
    finally:
        # Ejecuta siempre al cerrar el bloque
        logger_prueba.info("Fin de prueba del Paso 1.")

    print("\n--- Paso 2: Crear una subclase mínima para probar herencia y metadatos ---")
    # Define una clase concreta temporal solo para comprobar EntidadBase
    class EntidadDemo(EntidadBase):
        """Subclase concreta de prueba para EntidadBase."""

        def resumen(self) -> str:
            """Implementación mínima de resumen()."""
            # Retorna resumen con ID y estado
            estado = "Activa" if self._activa else "Inactiva"
            return f"[EntidadDemo {self._id_entidad}] Estado: {estado}"

    try:
        # Crea una instancia válida de prueba
        demo = EntidadDemo("demo-001")
        # Muestra resumen y metadatos base
        print(" ", demo.resumen())
        print("  Metadatos:", demo.metadatos_base())
        # Desactiva la entidad y verifica el cambio
        demo.desactivar()
        print("  Tras desactivar:", demo.resumen())
    except ErrorSoftwareFJ as exc:
        # Captura errores del dominio si ocurrieran
        print(f"  Error de dominio: {exc}")
        logger_prueba.error("Error en EntidadDemo: %s", exc)
    else:
        # Registra éxito si todo se ejecutó sin excepciones
        logger_prueba.info("Prueba de EntidadDemo exitosa para ID %s", demo.id_entidad)
    finally:
        # Cierra el ciclo de prueba del Paso 2
        logger_prueba.info("Fin de prueba del Paso 2.")

    print("\n--- Paso 3: Validar error por ID vacío y encadenamiento de excepciones ---")
    try:
        # Intenta crear una entidad con ID vacío para provocar ErrorValidacionDato
        _ = EntidadDemo("   ")
    except ErrorValidacionDato as exc:
        print(f"  Error de validación capturado: {exc}")
        logger_prueba.error("ID inválido rechazado: %s", exc)

    try:
        # Demuestra encadenamiento de excepciones con 'raise ... from causa'
        try:
            _ = int("abc")
        except ValueError as causa:
            raise ErrorCalculoInconsistente("Error al procesar dato numérico base") from causa
    except ErrorCalculoInconsistente as exc_encadenada:
        print(f"  Excepción encadenada: {exc_encadenada} -> Causa: {exc_encadenada.__cause__}")
        logger_prueba.error(
            "Excepción encadenada en base: %s | Causa: %s",
            exc_encadenada,
            exc_encadenada.__cause__,
        )

    print("\nPruebas del punto 1 completadas correctamente.")


if __name__ == "__main__":
    probar_entidad_base_secuencialmente()