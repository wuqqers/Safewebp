// src/services/api.js
class ApiService {
  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000/api/v1';
    this.ws = null;
  }

  getDownloadUrl(path) {
    if (!path) return '';
    const cleanPath = path.startsWith('/') ? path.slice(1) : path;
    return `${this.baseUrl}/${cleanPath}`;
  }

  async convertImages(files, settings, onProgress) {
    // WebSocket bağlantısını kur
    this.setupWebSocket(onProgress);

    const formData = new FormData();
    
    // Her dosyayı ayrı ayrı ekle
    files.forEach(file => {
      formData.append('images', file);
    });

    // Settings'i string olarak ekle
    const settingsData = {
      quality: parseInt(settings.quality) || 80,
      preserve_metadata: Boolean(settings.preserve_metadata),
      smart_optimize: Boolean(settings.smart_optimize)
    };
    
    formData.append('conversion_settings', JSON.stringify(settingsData));

    try {
      const response = await fetch(`${this.baseUrl}/convert-batch`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const data = await response.json();
        console.error('Server error response:', data);
        throw new Error(data.detail || 'Conversion failed');
      }

      const data = await response.json();
      return {
        ...data,
        files: data.files.map(file => ({
          ...file,
          output_path: this.getDownloadUrl(file.output_path)
        }))
      };
    } catch (error) {
      console.error('Conversion error details:', error);
      throw error;
    } finally {
      // İşlem bittiğinde WebSocket'i kapat
      this.closeWebSocket();
    }
  }

  setupWebSocket(onProgress) {
    if (this.ws) {
      this.ws.close();
    }

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onProgress(data);
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket connection closed');
    };
  }

  closeWebSocket() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const apiService = new ApiService();