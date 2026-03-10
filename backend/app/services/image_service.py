"""
Módulo de gestión de imágenes para entidades del sistema eléctrico.

Provee la clase ImageService, que encapsula las operaciones de almacenamiento
y recuperación de imágenes en el sistema de archivos local (directorio
``storage/``). Soporta imágenes de transformadores, planos unifilares,
barras y circuitos, organizadas por tipo de entidad e identificador.
"""

import os
import shutil
from pathlib import Path
from fastapi import UploadFile

from app.config import settings


class ImageService:
    """
    Servicio de gestión de imágenes para entidades del sistema eléctrico.

    Administra el ciclo de vida de las imágenes asociadas a transformadores,
    planos unifilares, barras y circuitos. Las imágenes se almacenan en el
    sistema de archivos local bajo el directorio definido por
    ``settings.STORAGE_PATH``, con una estructura de subdirectorios por
    tipo de entidad e identificador.

    Cada entidad mantiene un único archivo de imagen activa con nombre
    ``current.<ext>``, lo que simplifica la recuperación y garantiza que
    no se acumulen versiones anteriores.

    Class Attributes:
        ALLOWED_EXTENSIONS (set): Conjunto de extensiones de archivo
            permitidas para las imágenes subidas.
        MAX_SIZE (int): Tamaño máximo permitido en bytes, calculado a partir
            de ``settings.MAX_IMAGE_SIZE_MB``.
    """

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    MAX_SIZE = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024  # bytes

    @staticmethod
    def _get_directory(entity_type: str, entity_id: int, sub_id: int | None = None) -> Path:
        """
        Construye la ruta del directorio de almacenamiento para una entidad dada.

        La estructura de directorios es la siguiente:
        - ``unifilar``:    ``storage/imagenes-unifilares/<entity_id>/``
        - ``transformer``: ``storage/fotos-transformadores/<entity_id>/``
        - ``bar``:         ``storage/imagenes-barras/<entity_id>/<sub_id>/``
        - ``circuit``:     ``storage/imagenes-circuitos/<entity_id>/<sub_id>/``

        Args:
            entity_type (str): Tipo de entidad. Valores válidos: ``'unifilar'``,
                ``'transformer'``, ``'bar'``, ``'circuit'``.
            entity_id (int): Identificador primario de la entidad propietaria
                de la imagen.
            sub_id (int | None): Identificador secundario utilizado como
                subdirectorio adicional para barras y circuitos. Si es
                ``None``, se usa una cadena vacía como nombre de subdirectorio.

        Returns:
            Path: Ruta absoluta al directorio de almacenamiento de la imagen.

        Raises:
            ValueError: Si ``entity_type`` no corresponde a ninguno de los
                tipos de entidad soportados.
        """
        base = Path(settings.STORAGE_PATH)

        # Seleccionar el subdirectorio raíz según el tipo de entidad
        if entity_type == "unifilar":
            return base / "imagenes-unifilares" / str(entity_id)
        elif entity_type == "transformer":
            return base / "fotos-transformadores" / str(entity_id)
        elif entity_type == "bar":
            # Las barras pueden tener un nivel adicional de subdirectorio con sub_id
            return base / "imagenes-barras" / str(entity_id) / str(sub_id or "")
        elif entity_type == "circuit":
            # Los circuitos también admiten un subdirectorio secundario con sub_id
            return base / "imagenes-circuitos" / str(entity_id) / str(sub_id or "")

        raise ValueError(f"Tipo de entidad desconocido: {entity_type}")

    def get_image_path(self, entity_type: str, entity_id: int, sub_id: int | None = None) -> Path | None:
        """
        Retorna la ruta al archivo de imagen activa de una entidad, si existe.

        Busca en el directorio correspondiente un archivo con nombre
        ``current`` y cualquiera de las extensiones permitidas. Retorna la
        primera coincidencia encontrada.

        Args:
            entity_type (str): Tipo de entidad propietaria de la imagen.
            entity_id (int): Identificador primario de la entidad.
            sub_id (int | None): Identificador secundario para barras
                y circuitos. Por defecto ``None``.

        Returns:
            Path | None: Ruta absoluta al archivo de imagen si existe;
                ``None`` si el directorio no existe o no contiene ninguna
                imagen con las extensiones permitidas.
        """
        # Obtener el directorio calculado para esta entidad
        directory = self._get_directory(entity_type, entity_id, sub_id)

        # Si el directorio no existe, no hay imagen almacenada
        if not directory.exists():
            return None

        # Buscar un archivo 'current' con alguna de las extensiones permitidas
        for ext in self.ALLOWED_EXTENSIONS:
            path = directory / f"current{ext}"
            if path.exists():
                return path

        return None

    async def replace_image(
        self, entity_type: str, entity_id: int, file: UploadFile, sub_id: int | None = None
    ) -> Path:
        """
        Reemplaza la imagen activa de una entidad con un nuevo archivo subido.

        Valida la extensión y el tamaño del archivo recibido, elimina la
        imagen anterior si existe y guarda el nuevo archivo con el nombre
        estandarizado ``current.<ext>`` en el directorio correspondiente.

        Args:
            entity_type (str): Tipo de entidad para la que se sube la imagen.
            entity_id (int): Identificador primario de la entidad propietaria.
            file (UploadFile): Objeto de archivo recibido desde el endpoint
                de FastAPI, con nombre y contenido binario.
            sub_id (int | None): Identificador secundario para barras y
                circuitos. Por defecto ``None``.

        Returns:
            Path: Ruta absoluta al archivo de imagen guardado correctamente.

        Raises:
            ValueError: Si la extensión del archivo no está entre las
                permitidas (``ALLOWED_EXTENSIONS``).
            ValueError: Si el contenido del archivo supera el tamaño máximo
                definido por ``MAX_SIZE``.
        """
        # Extraer y normalizar la extensión del archivo recibido
        ext = Path(file.filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Extension no permitida: {ext}")

        # Resolver el directorio de destino y crearlo si no existe
        directory = self._get_directory(entity_type, entity_id, sub_id)
        directory.mkdir(parents=True, exist_ok=True)

        # Eliminar la imagen anterior para todas las extensiones posibles
        for old_ext in self.ALLOWED_EXTENSIONS:
            old_path = directory / f"current{old_ext}"
            if old_path.exists():
                old_path.unlink()

        # Leer el contenido del archivo y verificar que no supere el límite de tamaño
        new_path = directory / f"current{ext}"
        content = await file.read()
        if len(content) > self.MAX_SIZE:
            raise ValueError(f"Imagen excede el tamano maximo de {settings.MAX_IMAGE_SIZE_MB}MB")

        # Escribir el contenido binario en el archivo de destino
        with open(new_path, "wb") as f:
            f.write(content)

        return new_path
