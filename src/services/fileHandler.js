// src/services/fileHandler.js
export const formatFileSize = (bytes) => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(2)} ${units[unitIndex]}`;
  };
  
  export const validateImageFile = (file) => {
    const validTypes = [
      'image/jpeg',
      'image/png',
      'image/gif',
      'image/webp',
      'image/heic'
    ];
    
    return validTypes.includes(file.type);
  };
  
  export const processFiles = (files) => {
    return files.map(file => ({
      name: file.name,
      size: formatFileSize(file.size),
      type: file.type,
      preview: URL.createObjectURL(file)
    }));
  };