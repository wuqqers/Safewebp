// src/services/api.js
class ApiService {
  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'https://safeewebp-backend.onrender.com/api/v1';
    this.ws = null;
  }

  getDownloadUrl(path) {
    if (!path) return '';
    // Ensure full URL is returned
    const baseUrl = this.baseUrl.replace('/api/v1', '');
    const cleanPath = path.startsWith('/') ? path.slice(1) : path;
    const fullUrl = `${baseUrl}/${cleanPath}`;
    // Remove duplicate slashes, keeping protocol intact
    return fullUrl.replace(/([^:]\/)\/+/g, "$1");
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
      console.log('Making request to:', `${this.baseUrl}/convert-batch`); // Debug için

      const response = await fetch(`${this.baseUrl}/convert-batch`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        mode: 'cors',
        body: formData
      });

      if (!response.ok) {
        const data = await response.json();
        console.error('Server error response:', data);
        throw new Error(data.detail || 'Conversion failed');
      }

      const data = await response.json();
      
      // URL'leri düzelt
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
    }
  }

  setupWebSocket(onProgress) {
    if (this.ws) {
      this.ws.close();
    }

    // WebSocket URL'ini baseUrl'den türet
    const wsUrl = this.baseUrl.replace('http:', 'ws:').replace('https:', 'wss:');
    const wsEndpoint = `${wsUrl.replace('/api/v1', '')}/ws`;
    
    console.log('Connecting to WebSocket:', wsEndpoint); // Debug için

    this.ws = new WebSocket(wsEndpoint);
    
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
      // Yeniden bağlanmayı dene
      setTimeout(() => this.setupWebSocket(onProgress), 3000);
    };

    this.ws.onopen = () => {
      console.log('WebSocket connection established');
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