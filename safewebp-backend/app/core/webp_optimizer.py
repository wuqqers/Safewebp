import math

class WebPOptimizer:
    def calculate_optimal_quality(self, image_size, file_size, base_quality, smart_optimize=True):
        """Dosya boyutu ve görüntü boyutuna göre optimal kalite hesapla"""
        if not smart_optimize:
            return base_quality
            
        # Görüntü boyutu analizi
        total_pixels = image_size[0] * image_size[1]
        size_factor = min(1.0, math.sqrt(total_pixels / (4000 * 3000)))
        
        # Dosya boyutu analizi (MB cinsinden)
        file_size_mb = file_size / (1024 * 1024)
        
        # Akıllı boyut cezası hesaplama
        if file_size_mb > 5:
            size_penalty = min(30, (file_size_mb - 5) * 3)
        else:
            size_penalty = max(0, (file_size_mb - 2) * 2)
        
        # Boyuta göre minimum kalite belirleme
        if total_pixels > 4000 * 3000:  # 4K üzeri
            min_quality = 60
            max_quality = 85
        elif total_pixels > 1920 * 1080:  # Full HD üzeri
            min_quality = 65
            max_quality = 90
        else:
            min_quality = 70
            max_quality = 95
        
        # Kalite hesaplama
        optimal_quality = base_quality - size_penalty
        optimal_quality *= size_factor
        
        # Sınırları uygula
        optimal_quality = max(min_quality, min(max_quality, optimal_quality))
        
        return int(optimal_quality)

    def get_webp_params(self, quality, analysis_results):
        """WebP parametrelerini belirle"""
        # Temel parametreler
        params = {
            'quality': quality,
            'method': 6,  # En iyi sıkıştırma metodu
            'lossless': False,
            'exact': False,
            'minimize_size': True,
            'subsampling': 0,  # En iyi renk örneklemesi
            'use_sharp_yuv': True,
        }
        
        # Fotoğraf tipi analizi
        is_photo = analysis_results.get('is_photo', True)
        total_pixels = analysis_results.get('total_pixels', 0)
        
        # Yüksek kalite ayarları (95-100)
        if quality >= 95:
            params.update({
                'method': 6,
                'exact': True,
                'lossless': True,
                'subsampling': 0,
                'use_sharp_yuv': True,
                'kmin': 1,
                'kmax': 20,
                'filter_strength': 40,
                'filter_sharpness': 7,
                'filter_type': 1,
                'autofilter': True,
                'partitions': 0,
                'segments': 4,
                'pass': 2,
                'preprocessing': 0,
                'show_compressed': True
            })
            
        # Orta-yüksek kalite ayarları (85-94)
        elif quality >= 85:
            params.update({
                'method': 6,
                'exact': True,
                'lossless': False,
                'subsampling': 0,
                'use_sharp_yuv': True,
                'kmin': 2,
                'kmax': 15,
                'filter_strength': 30,
                'filter_sharpness': 5,
                'filter_type': 1,
                'autofilter': True,
                'partitions': 0,
                'segments': 4,
                'pass': 1,
                'preprocessing': 1 if is_photo else 0,
                'show_compressed': True
            })
            
        # Düşük-orta kalite ayarları (70-84)
        elif quality >= 70:
            params.update({
                'method': 4,
                'exact': False,
                'lossless': False,
                'subsampling': 1,
                'use_sharp_yuv': True,
                'kmin': 3,
                'kmax': 10,
                'filter_strength': 20,
                'filter_sharpness': 3,
                'filter_type': 0,
                'autofilter': True,
                'partitions': 0,
                'segments': 2,
                'pass': 1,
                'preprocessing': 1,
            })
            
        # Düşük kalite ayarları (0-69)
        else:
            params.update({
                'method': 3,
                'exact': False,
                'lossless': False,
                'subsampling': 2,
                'use_sharp_yuv': False,
                'kmin': 3,
                'kmax': 8,
                'filter_strength': 10,
                'filter_sharpness': 2,
                'filter_type': 0,
                'autofilter': True,
                'partitions': 0,
                'segments': 2,
                'pass': 1,
                'preprocessing': 1,
            })

        # Preset seçimi
        if is_photo:
            params['preset'] = 'photo'
        elif total_pixels < 512 * 512:
            params['preset'] = 'icon'
        else:
            params['preset'] = 'picture'

        # PIL.Image.save() için uyumlu olmayan parametreleri kaldır
        safe_params = {
            'quality': params['quality'],
            'method': params['method'],
            'lossless': params['lossless'],
            'exact': params['exact']
        }

        return safe_params