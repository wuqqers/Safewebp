# app/core/ml_optimizer.py
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
from pathlib import Path
import cv2
from typing import Dict, Tuple
import os

class MLOptimizer:
    def __init__(self, model_path: str = "models/optimizer_model.joblib"):
        self.model_path = Path(model_path)
        self.model = self._load_or_create_model()
        self.training_data = []
        
    def _load_or_create_model(self) -> RandomForestRegressor:
        """Mevcut modeli yükle veya yeni model oluştur"""
        if self.model_path.exists():
            return joblib.load(self.model_path)
        
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        return model

    def extract_features(self, image: np.ndarray) -> Dict[str, float]:
        """Görüntüden özellik çıkarımı yap"""
        # Temel özellikler
        height, width = image.shape[:2]
        total_pixels = height * width
        
        # Kenar tespiti
        edges = cv2.Canny(image, 100, 200)
        edge_density = np.count_nonzero(edges) / total_pixels
        
        # Renk karmaşıklığı
        if len(image.shape) == 3:
            color_std = np.std(image, axis=(0,1)).mean()
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            saturation = hsv[:,:,1].mean()
        else:
            color_std = np.std(image)
            saturation = 0
        
        # Doku analizi
        texture = np.std(cv2.Laplacian(image, cv2.CV_64F))
        
        return {
            'size': total_pixels,
            'aspect_ratio': width / height,
            'edge_density': edge_density,
            'color_complexity': color_std,
            'saturation': saturation,
            'texture_complexity': texture
        }

    def predict_optimal_params(self, image: np.ndarray) -> Tuple[int, dict]:
        """Optimal WebP parametrelerini tahmin et"""
        try:
            features = self.extract_features(image)
            
            # Model henüz eğitilmemişse veya hata varsa varsayılan değerleri kullan
            if not hasattr(self.model, 'predict') or True:  # Şimdilik her zaman varsayılan kullan
                # Görüntü özelliklerine göre basit bir kalite tahmini
                if features['edge_density'] > 0.1:
                    quality = 85  # Detaylı görüntüler için daha yüksek kalite
                elif features['color_complexity'] > 50:
                    quality = 80  # Karmaşık renkli görüntüler için orta-yüksek kalite
                else:
                    quality = 75  # Basit görüntüler için normal kalite
                    
                params = {
                    'quality': quality,
                    'method': 6 if features['edge_density'] > 0.1 else 4,
                    'lossless': False,
                    'exact': features['texture_complexity'] > 50
                }
                
                return quality, params
                
            # ML model hazır olduğunda bu kısmı kullan
            feature_vector = np.array([[
                features['size'],
                features['aspect_ratio'],
                features['edge_density'],
                features['color_complexity'],
                features['saturation'],
                features['texture_complexity']
            ]])
            quality = int(self.model.predict(feature_vector)[0])
            
            return quality, self._get_webp_params(quality, features)
            
        except Exception as e:
            print(f"Error in predict_optimal_params: {str(e)}")
            # Hata durumunda varsayılan değerleri döndür
            return 80, {
                'quality': 80,
                'method': 4,
                'lossless': False,
                'exact': False
            }

    def _get_webp_params(self, quality: int, features: Dict[str, float]) -> dict:
        """Özeliklere göre WebP parametrelerini optimize et"""
        params = {
            'quality': quality,
            'method': 6,
            'lossless': False,
            'exact': False
        }
        
        # Kenar yoğunluğuna göre method seçimi
        if features['edge_density'] > 0.1:
            params['method'] = 6
        else:
            params['method'] = 4
            
        # Renk karmaşıklığına göre lossless seçimi
        if features['color_complexity'] < 30 and features['texture_complexity'] < 10:
            params['lossless'] = True
            
        # Doku karmaşıklığına göre exact seçimi
        if features['texture_complexity'] > 50:
            params['exact'] = True
            
        return params

    def train(self, image_data: np.ndarray, quality_score: float, compression_ratio: float):
        """Modeli yeni verilerle eğit"""
        try:
            features = self.extract_features(image_data)
            self.training_data.append({
                'features': list(features.values()),
                'quality': quality_score,
                'compression': compression_ratio
            })
            
            # Belirli sayıda veri toplandığında modeli güncelle
            if len(self.training_data) >= 10:
                self._update_model()
        except Exception as e:
            print(f"Error in train: {str(e)}")
            
    def _update_model(self):
        """Modeli toplanan verilerle güncelle"""
        try:
            if not self.training_data:
                return
                
            X = np.array([data['features'] for data in self.training_data])
            y = np.array([data['quality'] for data in self.training_data])
            
            if not hasattr(self.model, 'predict'):
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                
            self.model.fit(X, y)
            joblib.dump(self.model, self.model_path)
            self.training_data = []  # Veriyi temizle
        except Exception as e:
            print(f"Error in _update_model: {str(e)}")