from __future__ import annotations

from functools import singledispatchmethod
import logging
from typing import Any, Dict, Optional


# ==============================================================================
# EXCEPCIONES DEL DOMINIO (COMPATIBLES CON EL RESTO DEL PROYECTO)
# ==============================================================================
class ErrorSoftwareFJ(Exception):
    """Excepción base para errores del sistema Software FJ."""


class ErrorValidacionDato(ErrorSoftwareFJ):
    """Se lanza cuando un parámetro de entrada no cumple con las reglas."""


class ErrorCalculoInconsistente(ErrorSoftwareFJ):
    """Se lanza cuando un porcentaje, monto o resultado financiero es inválido."""


# ==============================================================================
# PUNTO 5: CLASE CON MÉTODOS SOBRECARGADOS PARA CÁLCULO DE COSTOS
# ==============================================================================
class CalculadorCostos:
    """Gestiona variantes sobrecargadas para calcular costos, impuestos y descuentos."""

    # Constante con la tarifa estándar de IVA en Colombia (19%)
    IVA_ESTANDAR: float = 19.0

    def __init__(self, impuesto_defecto: float = IVA_ESTANDAR) -> None:
        # Valida que el impuesto por defecto esté entre 0 y 100
        self._validar_porcentaje(impuesto_defecto, "impuesto por defecto")
        # Almacena el impuesto predeterminado para el calculador
        self._impuesto_defecto: float = float(impuesto_defecto)

    @staticmethod
    def _validar_porcentaje(valor: Any, nombre_campo: str) -> float:
        """Valida que un porcentaje sea numérico y esté en el rango [0, 100]."""
        # Verifica que el valor sea entero o flotante (excluyendo booleanos)
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            # Lanza error si el tipo de dato no es numérico
            raise ErrorValidacionDato(f"El {nombre_campo} debe ser un valor numérico.")
        # Comprueba que el porcentaje esté dentro de los límites permitidos
        if not (0.0 <= float(valor) <= 100.0):
            # Lanza error si el porcentaje es negativo o mayor al 100%
            raise ErrorCalculoInconsistente(
                f"El {nombre_campo} ({valor}%) debe estar entre 0% y 100%."
            )
        # Retorna el porcentaje convertido a flotante
        return float(valor)

    @staticmethod
    def _validar_monto_no_negativo(valor: Any, nombre_campo: str) -> float:
        """Valida que un monto monetario sea numérico y mayor o igual a cero."""
        # Verifica que el valor sea numérico y no booleano
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            # Lanza error de validación de tipo
            raise ErrorValidacionDato(f"El {nombre_campo} debe ser un valor numérico.")
        # Comprueba que el monto no sea negativo
        if float(valor) < 0.0:
            # Impide montos negativos en tarifas o recargos
            raise ErrorCalculoInconsistente(
                f"El {nombre_campo} (${valor}) no puede ser negativo."
            )
        # Retorna el monto como flotante
        return float(valor)

    # --------------------------------------------------------------------------
    # SOBRECARGA 1: Por parámetros opcionales y argumentos variables
    # --------------------------------------------------------------------------
    def calcular(
        self,
        tarifa_unitaria: float,
        duracion: int = 1,
        cantidad: int = 1,
        descuento_pct: Optional[float] = None,
        impuesto_pct: Optional[float] = None,
        recargo_fijo: float = 0.0,
        exento_impuesto: bool = False,
    ) -> float:
        """
        Método sobrecargado mediante parámetros opcionales:
        - calcular(tarifa) -> cobra 1 unidad con impuesto por defecto
        - calcular(tarifa, duracion) -> multiplica por duración
        - calcular(tarifa, duracion, cantidad, descuento_pct=10) -> aplica descuento
        - calcular(..., exento_impuesto=True) -> omite el impuesto
        """
        # Valida la tarifa unitaria (debe ser estrictamente mayor a cero)
        tarifa = self._validar_monto_no_negativo(tarifa_unitaria, "tarifa unitaria")
        if tarifa <= 0.0:
            # Rechaza tarifas iguales a cero
            raise ErrorCalculoInconsistente("La tarifa unitaria debe ser mayor que cero.")

        # Valida que la duración sea un entero positivo
        if isinstance(duracion, bool) or not isinstance(duracion, int) or duracion <= 0:
            # Lanza error si la duración no es un entero positivo
            raise ErrorValidacionDato("La duración debe ser un número entero mayor que cero.")

        # Valida que la cantidad sea un entero positivo
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            # Lanza error si la cantidad no es un entero positivo
            raise ErrorValidacionDato("La cantidad debe ser un número entero mayor que cero.")

        # Valida el recargo fijo opcional
        recargo = self._validar_monto_no_negativo(recargo_fijo, "recargo fijo")

        # Determina el porcentaje de descuento (0.0 si no se envió)
        desc = 0.0 if descuento_pct is None else self._validar_porcentaje(descuento_pct, "descuento")

        # Determina el porcentaje de impuesto según si está exento o usa el valor por defecto
        if exento_impuesto:
            imp = 0.0
        elif impuesto_pct is None:
            imp = self._impuesto_defecto
        else:
            imp = self._validar_porcentaje(impuesto_pct, "impuesto")

        # Ejecuta el cálculo en bloque try/except para encadenar fallos inesperados
        try:
            # Calcula el monto bruto multiplicando tarifa, duración y cantidad
            monto_bruto = tarifa * duracion * cantidad
            # Suma el recargo adicional si existe
            subtotal = monto_bruto + recargo
            # Aplica el descuento porcentual sobre el subtotal
            monto_con_descuento = subtotal * (1.0 - (desc / 100.0))
            # Aplica el impuesto porcentual sobre el monto ya descontado
            total_final = monto_con_descuento * (1.0 + (imp / 100.0))

            # Verifica consistencia final del resultado
            if total_final < 0.0:
                # Lanza error si el total final es negativo
                raise ErrorCalculoInconsistente("El total calculado resultó negativo.")

            # Retorna el total redondeado a 2 decimales
            return round(total_final, 2)
        except ErrorSoftwareFJ:
            # Propaga excepciones controladas del dominio
            raise
        except Exception as exc:
            # Encadena cualquier error imprevisto conservando la causa original
            raise ErrorCalculoInconsistente("Fallo inesperado en el cálculo de costos.") from exc

    # --------------------------------------------------------------------------
    # SOBRECARGA 2: Por tipo de entrada usando @singledispatchmethod
    # --------------------------------------------------------------------------
    @singledispatchmethod
    def cotizar(self, datos: Any) -> Dict[str, float]:
        """Despacha la cotización según el tipo de estructura recibida."""
        # Lanza error si se recibe un tipo de dato no soportado
        raise ErrorValidacionDato(
            f"Tipo de dato no soportado para cotizar: {type(datos).__name__}."
        )

    @cotizar.register
    def _(self, datos: float) -> Dict[str, float]:
        """Sobrecarga para recibir directamente un monto base flotante."""
        # Valida el monto base recibido
        base = self._validar_monto_no_negativo(datos, "monto base")
        if base <= 0.0:
            raise ErrorCalculoInconsistente("El monto base debe ser mayor que cero.")
        # Calcula el impuesto estándar sobre la base
        valor_impuesto = round(base * (self._impuesto_defecto / 100.0), 2)
        # Retorna el desglose financiero
        return {
            "subtotal": round(base, 2),
            "descuento": 0.0,
            "impuesto": valor_impuesto,
            "total": round(base + valor_impuesto, 2),
        }

    @cotizar.register
    def _(self, datos: int) -> Dict[str, float]:
        """Sobrecarga para recibir directamente un monto base entero."""
        # Reutiliza la implementación flotante convirtiendo el entero
        return self.cotizar(float(datos))

    @cotizar.register
    def _(self, datos: dict) -> Dict[str, float]:
        """Sobrecarga para recibir un diccionario completo con parámetros de cotización."""
        # Verifica que existan las claves mínimas requeridas en el diccionario
        if "tarifa" not in datos:
            # Lanza error si falta la clave obligatoria 'tarifa'
            raise ErrorValidacionDato("El diccionario de cotización requiere la clave 'tarifa'.")

        # Extrae valores del diccionario con respaldos por defecto
        tarifa = datos["tarifa"]
        duracion = datos.get("duracion", 1)
        cantidad = datos.get("cantidad", 1)
        descuento_pct = datos.get("descuento_pct", 0.0)
        impuesto_pct = datos.get("impuesto_pct", self._impuesto_defecto)
        recargo_fijo = datos.get("recargo_fijo", 0.0)

        # Valida los campos usando el método principal
        total = self.calcular(
            tarifa_unitaria=tarifa,
            duracion=duracion,
            cantidad=cantidad,
            descuento_pct=descuento_pct,
            impuesto_pct=impuesto_pct,
            recargo_fijo=recargo_fijo,
        )

        # Calcula el desglose paso a paso para retornarlo detallado
        subtotal = round((float(tarifa) * int(duracion) * int(cantidad)) + float(recargo_fijo), 2)
        valor_descuento = round(subtotal * (float(descuento_pct) / 100.0), 2)
        base_gravable = round(subtotal - valor_descuento, 2)
        valor_impuesto = round(base_gravable * (float(impuesto_pct) / 100.0), 2)

        # Retorna diccionario con el desglose completo
        return {
            "subtotal": subtotal,
            "descuento": valor_descuento,
            "impuesto": valor_impuesto,
            "total": total,
        }


# ==============================================================================
# EJECUCIÓN SECUENCIAL DE PRUEBAS PARA EL PUNTO 5
# ==============================================================================
def probar_calculador_secuencialmente() -> None:
    """Ejecuta pruebas paso a paso de todas las sobrecargas y validaciones."""
    # Configura logger de prueba en archivo
    log_calc = logging.getLogger("PruebaCalculador")
    log_calc.setLevel(logging.INFO)
    if not log_calc.handlers:
        handler = logging.FileHandler("prueba_calculador.log", mode="a", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        log_calc.addHandler(handler)

    # Instancia el calculador con IVA por defecto del 19%
    calc = CalculadorCostos(impuesto_defecto=19.0)

    print("--- Paso 1: Llamadas sobrecargadas a calcular() ---")
    # Variante A: Solo tarifa (1 unidad, 1 hora/día, IVA 19%)
    v1 = calc.calcular(100000.0)
    print(f"  Variante 1 (solo tarifa $100,000 + IVA): ${v1:,.2f}")

    # Variante B: Tarifa + duración (3 horas, IVA 19%)
    v2 = calc.calcular(80000.0, duracion=3)
    print(f"  Variante 2 (tarifa $80,000 x 3h + IVA): ${v2:,.2f}")

    # Variante C: Tarifa + duración + cantidad + descuento + recargo
    v3 = calc.calcular(
        tarifa_unitaria=50000.0,
        duracion=2,
        cantidad=3,
        descuento_pct=15.0,
        recargo_fijo=20000.0,
    )
    print(f"  Variante 3 (3 und x 2d + recargo - 15% desc + IVA): ${v3:,.2f}")

    # Variante D: Servicio exento de impuesto
    v4 = calc.calcular(120000.0, duracion=2, exento_impuesto=True)
    print(f"  Variante 4 (exento de IVA): ${v4:,.2f}")
    log_calc.info("Variantes de calcular() ejecutadas correctamente.")

    print("\n--- Paso 2: Llamadas sobrecargadas por tipo a cotizar() ---")
    # Sobrecarga con número entero
    print("  Cotizar entero (200000):", calc.cotizar(200000))
    # Sobrecarga con número flotante
    print("  Cotizar flotante (150000.5):", calc.cotizar(150000.5))
    # Sobrecarga con diccionario completo
    print(
        "  Cotizar diccionario:",
        calc.cotizar(
            {
                "tarifa": 90000.0,
                "duracion": 4,
                "cantidad": 1,
                "descuento_pct": 10.0,
                "impuesto_pct": 19.0,
            }
        ),
    )

    print("\n--- Paso 3: Manejo de errores en porcentajes, tipos y encadenamiento ---")
    # Prueba descuento inválido (> 100%)
    try:
        calc.calcular(50000.0, descuento_pct=150.0)
    except ErrorCalculoInconsistente as exc:
        print(f"  Error de porcentaje capturado: {exc}")
        log_calc.error("Descuento inválido: %s", exc)

    # Prueba tipo no soportado en cotizar()
    try:
        calc.cotizar(["lista_no_valida"])
    except ErrorValidacionDato as exc:
        print(f"  Error de tipo en sobrecarga capturado: {exc}")
        log_calc.error("Tipo inválido en cotizar(): %s", exc)

    # Prueba encadenamiento de excepciones con raise ... from
    try:
        try:
            _ = float("tarifa_corrupta")
        except ValueError as causa:
            raise ErrorCalculoInconsistente("No se pudo interpretar la tarifa ingresada") from causa
    except ErrorCalculoInconsistente as exc_enc:
        print(f"  Excepción encadenada: {exc_enc} -> Causa: {exc_enc.__cause__}")
        log_calc.error("Excepción encadenada: %s | Causa: %s", exc_enc, exc_enc.__cause__)

    print("\nPruebas del punto 5 completadas correctamente.")


if __name__ == "__main__":
    probar_calculador_secuencialmente()