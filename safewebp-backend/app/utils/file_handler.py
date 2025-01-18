# app/utils/file_handler.py
import os
import aiofiles
from pathlib import Path
from PIL import Image
import pillow_heif
from fastapi import UploadFile
from ..config import settings

class FileHandler:
    @staticmethod
    async def save_upload_file(upload_file: UploadFile) -> Path:
        """Yüklenen dosyayı kaydet"""
        file_path = settings.UPLOAD_DIR / upload_file.filename
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await upload_file.read(1024 * 1024):  # 1MB chunks
                await out_file.write(content)
                
        return file_path

    @staticmethod
    def validate_file(upload_file: UploadFile) -> bool:
        """Dosya uzantısını kontrol et"""
        ext = Path(upload_file.filename).suffix.lower()
        return ext in settings.ALLOWED_EXTENSIONS

    @staticmethod
    def process_heic_image(image_path: Path) -> Image.Image:
        """HEIC formatındaki görüntüleri işle"""
        try:
            heif_file = pillow_heif.read_heif(str(image_path))
            image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
            )
            return image
        except Exception as e:
            raise ValueError(f"HEIC işleme hatası: {str(e)}")

    @staticmethod
    def load_image(image_path: Path) -> Image.Image:
        """Görüntü dosyasını yükle"""
        try:
            if image_path.suffix.lower() == '.heic':
                return FileHandler.process_heic_image(image_path)
            return Image.open(image_path)
        except Exception as e:
            raise ValueError(f"Görüntü yükleme hatası: {str(e)}")

    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """Dosya boyutunu byte cinsinden döndür"""
        return os.path.getsize(file_path)

    @staticmethod
    def format_size(size: int) -> str:
        """Dosya boyutunu formatla"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"