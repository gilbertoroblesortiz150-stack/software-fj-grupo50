"""Punto 2: clase Cliente para el proyecto Software FJ.

Basado en la seccion CLIENTE de "codigo punto 2.docx".
Utiliza la clase abstracta compartida del punto 1.
"""

from __future__ import annotations

import hashlib
import hmac
import re

from clase_abstracta_general import EntidadBase, ErrorValidacionDato


class Cliente(EntidadBase):
    """Representa un cliente con datos validados y contrasena protegida."""

    def __init__(
        self,
        id: str,
        nombre: str,
        email: str,
        telefono: str,
        doc: str,
        clave: str,
    ) -> None:
        super().__init__(id)

        if not isinstance(nombre, str) or len(nombre.strip()) < 3:
            raise ErrorValidacionDato("El nombre debe tener al menos 3 caracteres.")
        if not isinstance(email, str) or not re.fullmatch(
            r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", email.strip()
        ):
            raise ErrorValidacionDato("El correo electronico es invalido.")

        # El telefono se conserva como texto para no perder ceros iniciales.
        telefono_str = str(telefono).strip()
        if not telefono_str.isdigit() or len(telefono_str) < 7:
            raise ErrorValidacionDato("El telefono debe tener al menos 7 digitos.")
        doc_str = str(doc).strip()
        if not doc_str.isdigit():
            raise ErrorValidacionDato("El documento debe contener digitos.")
        if not isinstance(clave, str) or not clave:
            raise ErrorValidacionDato("La clave no puede estar vacia.")

        self._id = self._id_entidad
        self._nombre = nombre.strip().title()
        self._email = email.strip().lower()
        self._telefono = telefono_str
        self._doc = doc_str
        # Se conserva el mecanismo SHA-256 utilizado por el codigo recibido.
        self._hash = hashlib.sha256(clave.encode("utf-8")).hexdigest()

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def email(self) -> str:
        return self._email

    @property
    def telefono(self) -> str:
        return self._telefono

    def verificar(self, clave: str) -> bool:
        """Comprueba la clave sin exponerla en texto claro."""
        if not isinstance(clave, str):
            return False
        digest = hashlib.sha256(clave.encode("utf-8")).hexdigest()
        return hmac.compare_digest(digest, self._hash)

    def describir(self) -> str:
        """Describe al cliente sin mostrar el documento completo."""
        return (
            f"Cliente [{self._id_entidad}] {self._nombre} - "
            f"{self._email} - Doc ***{self._doc[-3:]}"
        )

    def resumen(self) -> str:
        """Implementa el metodo abstracto requerido por EntidadBase."""
        return self.describir()


def probar_cliente() -> None:
    """Demuestra un registro valido y la captura de un registro invalido."""
    from clase_abstracta_general import configurar_logger

    logger = configurar_logger()
    try:
        cliente = Cliente(
            "C1", "Felipe Jimenez", "felipe@email.com", "3001234567",
            "1090456789", "clave123",
        )
    except ErrorValidacionDato as exc:
        logger.error("Fallo en registro de cliente: %s", exc)
    else:
        print(cliente.describir())
        print("Contrasena valida:", cliente.verificar("clave123"))
        print("Contrasena incorrecta:", cliente.verificar("otra-clave"))
    finally:
        logger.info("Prueba del registro valido finalizada")

    try:
        Cliente("C2", "Jo", "correo-invalido", "123", "12345", "x")
    except ErrorValidacionDato as exc:
        print("Validacion esperada:", exc)
        logger.warning("Registro invalido rechazado: %s", exc)


if __name__ == "__main__":
    probar_cliente()
