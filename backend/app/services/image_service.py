import os
import shutil
from pathlib import Path
from fastapi import UploadFile

from app.config import settings


class ImageService:
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    MAX_SIZE = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024  # bytes

    @staticmethod
    def _get_directory(entity_type: str, entity_id: int, sub_id: int | None = None) -> Path:
        base = Path(settings.STORAGE_PATH)
        if entity_type == "unifilar":
            return base / "imagenes-unifilares" / str(entity_id)
        elif entity_type == "transformer":
            return base / "fotos-transformadores" / str(entity_id)
        elif entity_type == "bar":
            return base / "imagenes-barras" / str(entity_id) / str(sub_id or "")
        elif entity_type == "circuit":
            return base / "imagenes-circuitos" / str(entity_id) / str(sub_id or "")
        raise ValueError(f"Tipo de entidad desconocido: {entity_type}")

    def get_image_path(self, entity_type: str, entity_id: int, sub_id: int | None = None) -> Path | None:
        directory = self._get_directory(entity_type, entity_id, sub_id)
        if not directory.exists():
            return None
        for ext in self.ALLOWED_EXTENSIONS:
            path = directory / f"current{ext}"
            if path.exists():
                return path
        return None

    async def replace_image(
        self, entity_type: str, entity_id: int, file: UploadFile, sub_id: int | None = None
    ) -> Path:
        ext = Path(file.filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Extension no permitida: {ext}")

        directory = self._get_directory(entity_type, entity_id, sub_id)
        directory.mkdir(parents=True, exist_ok=True)

        # Delete old image
        for old_ext in self.ALLOWED_EXTENSIONS:
            old_path = directory / f"current{old_ext}"
            if old_path.exists():
                old_path.unlink()

        # Save new image
        new_path = directory / f"current{ext}"
        content = await file.read()
        if len(content) > self.MAX_SIZE:
            raise ValueError(f"Imagen excede el tamano maximo de {settings.MAX_IMAGE_SIZE_MB}MB")

        with open(new_path, "wb") as f:
            f.write(content)

        return new_path
