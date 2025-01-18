# app/main.py
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    WebSocket,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Set
import asyncio
from pathlib import Path
import cv2
import numpy as np
import json

from .config import settings
from .schemas.image import (
    ConversionSettings,
    ConversionResponse,
    BatchConversionResponse,
)
from .utils.file_handler import FileHandler
from .core.image_processor import ImageProcessor
from .core.webp_optimizer import WebPOptimizer
from .core.ml_optimizer import MLOptimizer

app = FastAPI(title=settings.PROJECT_NAME)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statik dosya sunucusu
app.mount("/static", StaticFiles(directory="static"), name="static")

# Bağımlılıklar
file_handler = FileHandler()
image_processor = ImageProcessor()
webp_optimizer = WebPOptimizer()
ml_optimizer = MLOptimizer()

# WebSocket bağlantılarını tut
websocket_connections: Set[WebSocket] = set()

async def broadcast_progress(progress: dict):
    """Tüm WebSocket bağlantılarına ilerleme durumunu gönder"""
    dead_connections = set()
    for websocket in websocket_connections:
        try:
            await websocket.send_json(progress)
        except:
            dead_connections.add(websocket)

    # Kapalı bağlantıları temizle
    websocket_connections.difference_update(dead_connections)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket bağlantısını yönet"""
    await websocket.accept()
    websocket_connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        websocket_connections.remove(websocket)

@app.post("/api/v1/convert", response_model=ConversionResponse)
async def convert_single_image(
    image: UploadFile = File(...),
    conversion_settings: ConversionSettings = ConversionSettings(),
):
    """Tek bir görüntüyü WebP formatına dönüştür"""
    if not file_handler.validate_file(image):
        raise HTTPException(status_code=400, detail="Desteklenmeyen dosya formatı")

    try:
        # Dosyayı kaydet
        input_path = await file_handler.save_upload_file(image)
        original_size = file_handler.get_file_size(input_path)

        # Görüntüyü yükle ve analiz et
        img = file_handler.load_image(input_path)

        # OpenCV formatına dönüştür
        cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # ML model ile optimal parametreleri tahmin et
        optimal_quality, webp_params = ml_optimizer.predict_optimal_params(cv_image)

        if conversion_settings.smart_optimize:
            # ML tahminlerini kullan
            quality = optimal_quality
        else:
            # Kullanıcı ayarlarını kullan
            quality = conversion_settings.quality
            webp_params = webp_optimizer.get_webp_params(
                quality, {"is_photo": True}  # Basit varsayılan değer
            )

        # Görüntüyü optimize et
        img = image_processor.optimize_image_size(img, quality)
        img = image_processor.optimize_color_mode(img)

        # Çıktı dosya yolu
        output_filename = f"{input_path.stem}_optimized.webp"
        output_path = settings.UPLOAD_DIR / output_filename

        # WebP parametrelerini güncelle
        if conversion_settings.preserve_metadata:
            exif = img.info.get("exif")
            icc_profile = img.info.get("icc_profile")
            if exif is not None:
                webp_params["exif"] = exif
            if icc_profile is not None:
                webp_params["icc_profile"] = icc_profile

        # WebP olarak kaydet
        img.save(output_path, "webp", **webp_params)
        converted_size = file_handler.get_file_size(output_path)

        # Sonuçları hesapla
        reduction = ((original_size - converted_size) / original_size) * 100

        # Modeli eğit
        if conversion_settings.smart_optimize:
            quality_score = min(
                100, max(0, 100 - (reduction * 0.5))
            )  # Basit kalite skoru
            ml_optimizer.train(cv_image, quality_score, reduction / 100)

        # Dosyaları temizle
        if input_path.exists():
            input_path.unlink()

        return ConversionResponse(
            original_size=original_size,
            converted_size=converted_size,
            reduction_percent=reduction,
            output_path=f"/static/uploads/{output_filename}",
        )

    except Exception as e:
        # Hata durumunda dosyaları temizle
        if "input_path" in locals() and input_path.exists():
            input_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/convert-batch", response_model=BatchConversionResponse)
async def convert_batch_images(
    images: List[UploadFile] = File(...), 
    conversion_settings: str = Form(...)
):
    """Birden fazla görüntüyü WebP formatına dönüştür"""
    print("Received conversion settings:", conversion_settings)  # Debug için

    if not images:
        raise HTTPException(status_code=400, detail="Dosya yüklenmedi")

    try:
        # Settings'i parse et
        settings_dict = json.loads(conversion_settings)
        print("Parsed settings:", settings_dict)  # Debug için

        settings = ConversionSettings(**settings_dict)
        print("Converted to ConversionSettings:", settings)  # Debug için
    except Exception as e:
        print("Error parsing settings:", str(e))  # Debug için
        raise HTTPException(status_code=422, detail=f"Geçersiz ayarlar: {str(e)}")

    results = []
    total_original = 0
    total_converted = 0
    failed_files = []

    for index, image in enumerate(images):
        try:
            print(f"Processing image {index + 1}/{len(images)}: {image.filename}")  # Debug için

            # İlerleme durumunu başlangıçta gönder
            progress = {
                "current_file": image.filename,
                "progress": (index / len(images)) * 100,
                "total_files": len(images),
                "processed_files": index,
                "total_saved": total_original - total_converted,
            }
            await broadcast_progress(progress)

            # Görüntüyü dönüştür
            result = await convert_single_image(image, settings)
            print(f"Conversion result for {image.filename}:", result)  # Debug için

            results.append(result)

            total_original += result.original_size
            total_converted += result.converted_size

            # İlerleme durumunu güncelle
            progress.update({
                "progress": ((index + 1) / len(images)) * 100,
                "processed_files": index + 1,
                "total_saved": total_original - total_converted,
                "current_reduction": result.reduction_percent,
            })
            await broadcast_progress(progress)

        except Exception as e:
            import traceback
            print(f"Error processing {image.filename}:")
            print(traceback.format_exc())  # Detaylı hata mesajı
            
            failed_files.append({"filename": image.filename, "error": str(e)})
            continue

    if not results:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Hiçbir dosya dönüştürülemedi",
                "failed_files": failed_files,
            },
        )

    avg_reduction = (
        ((total_original - total_converted) / total_original) * 100
        if total_original > 0
        else 0
    )

    # Son durumu gönder
    final_progress = {
        "progress": 100,
        "total_files": len(images),
        "processed_files": len(results),
        "failed_files": len(failed_files),
        "total_saved": total_original - total_converted,
        "average_reduction": avg_reduction,
    }
    await broadcast_progress(final_progress)

    response = BatchConversionResponse(
        total_files=len(results),
        total_original_size=total_original,
        total_converted_size=total_converted,
        average_reduction=avg_reduction,
        files=results,
        failed_files=failed_files,
    )

    print("Final response:", response)  # Debug için
    return response

@app.get("/api/v1/health")
async def health_check():
    """API sağlık kontrolü"""
    return {
        "status": "healthy",
        "ml_model": "active" if ml_optimizer.model is not None else "initializing",
    }

# Temizlik işlevi
@app.on_event("startup")
async def startup_event():
    """Başlangıçta upload klasörünü temizle"""
    import shutil

    if settings.UPLOAD_DIR.exists():
        shutil.rmtree(settings.UPLOAD_DIR)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Kapanışta WebSocket bağlantılarını kapat"""
    for websocket in websocket_connections:
        try:
            await websocket.close()
        except:
            pass
    websocket_connections.clear()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)