from PIL import Image, ImageEnhance
import math

class ImageProcessor:
    def analyze_image(self, image):
        """Görüntü analizi yaparak optimal ayarları belirle"""
        width, height = image.size
        total_pixels = width * height
        
        # Renk analizi
        try:
            if image.mode == 'P':
                color_count = len(image.getcolors(maxcolors=256))
            else:
                converted = image.convert('P', palette=Image.Palette.ADAPTIVE, colors=256)
                color_count = len(converted.getcolors(maxcolors=256))
            
            is_photo = color_count is None or color_count > 192
        except:
            is_photo = True
        
        # Detay analizi
        edge_density = self._calculate_edge_density(image)
        
        return {
            'is_photo': is_photo,
            'total_pixels': total_pixels,
            'width': width,
            'height': height,
            'aspect_ratio': width / height,
            'mode': image.mode,
            'edge_density': edge_density,
            'color_complexity': color_count if isinstance(color_count, int) else 256
        }

    def optimize_image_size(self, image, quality):
        """Görüntü boyutunu optimize et"""
        width, height = image.size
        max_dimension = 5000  # Ultra HD için maksimum boyut
        min_dimension = 800   # Minimum kalite boyutu
        optimal_dimension = 3000  # Optimal boyut

        # Boyut optimizasyonu
        if max(width, height) > max_dimension:
            ratio = max_dimension / max(width, height)
            new_size = tuple(int(dim * ratio) for dim in (width, height))
            image = self._high_quality_resize(image, new_size)
        elif max(width, height) > optimal_dimension:
            if quality < 90:  # Yüksek kalite istenmiyor ise boyutu düşür
                ratio = optimal_dimension / max(width, height)
                new_size = tuple(int(dim * ratio) for dim in (width, height))
                image = self._high_quality_resize(image, new_size)
        elif max(width, height) < min_dimension and quality > 60:
            ratio = min_dimension / max(width, height)
            new_size = tuple(int(dim * ratio) for dim in (width, height))
            image = self._high_quality_resize(image, new_size)

        return image

    def _high_quality_resize(self, image, size):
        """Yüksek kaliteli boyutlandırma"""
        if image.mode == 'RGBA':
            # Alfa kanalını ayrı işle
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            resized_background = background.resize(size, Image.Resampling.LANCZOS)
            
            alpha = image.split()[3]
            resized_alpha = alpha.resize(size, Image.Resampling.LANCZOS)
            
            resized = resized_background.convert('RGBA')
            resized.putalpha(resized_alpha)
            
            return resized
        else:
            return image.resize(size, Image.Resampling.LANCZOS)

    def _calculate_edge_density(self, image):
        """Kenar yoğunluğunu hesapla"""
        if image.mode != 'L':
            image = image.convert('L')
        
        width, height = image.size
        pixels = image.load()
        edge_count = 0
        
        for y in range(1, height-1):
            for x in range(1, width-1):
                # Basit Sobel operatörü
                gx = pixels[x+1, y] - pixels[x-1, y]
                gy = pixels[x, y+1] - pixels[x, y-1]
                gradient = math.sqrt(gx*gx + gy*gy)
                if gradient > 30:  # Eşik değeri
                    edge_count += 1
        
        return edge_count / (width * height)

    def optimize_color_mode(self, image):
        """Renk modunu optimize et"""
        if image.mode == 'RGBA':
            alpha = image.getchannel('A')
            if alpha.getextrema()[0] == 255:  # Tamamen opak
                image = image.convert('RGB')
            else:
                # Yarı saydam pikselleri optimize et
                threshold = 128
                alpha_data = alpha.getdata()
                new_alpha = Image.new('L', alpha.size)
                new_alpha.putdata([255 if a > threshold else 0 for a in alpha_data])
                channels = list(image.split())
                channels[3] = new_alpha
                image = Image.merge('RGBA', channels)
        elif image.mode == 'P':
            if 'transparency' in image.info:
                image = image.convert('RGBA')
            else:
                image = image.convert('RGB')
        elif image.mode not in ['RGB', 'RGBA']:
            image = image.convert('RGB')

        return image