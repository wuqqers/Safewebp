// src/components/custom/FileUpload.js
"use client";
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Cloud, Image, X } from 'lucide-react';

export default function FileUpload({ onFilesSelected, onStatsUpdate, selectedFiles }) {
  const formatSize = (bytes) => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(2)} ${units[unitIndex]}`;
  };

  const onDrop = useCallback((acceptedFiles) => {
    onFilesSelected(acceptedFiles);
    const totalSize = acceptedFiles.reduce((acc, file) => acc + file.size, 0);
    onStatsUpdate(prev => ({
      ...prev,
      totalFiles: acceptedFiles.length,
      totalSize: formatSize(totalSize)
    }));
  }, [onFilesSelected, onStatsUpdate]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic']
    },
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  const removeFile = (indexToRemove) => {
    const newFiles = selectedFiles.filter((_, index) => index !== indexToRemove);
    onFilesSelected(newFiles);
    
    const totalSize = newFiles.reduce((acc, file) => acc + file.size, 0);
    onStatsUpdate(prev => ({
      ...prev,
      totalFiles: newFiles.length,
      totalSize: formatSize(totalSize)
    }));
  };

  const files = Array.isArray(selectedFiles) ? selectedFiles : [];

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-8 
          transition-all duration-200 ease-in-out
          cursor-pointer group
          ${isDragActive 
            ? 'border-indigo-500 bg-indigo-500/10' 
            : 'border-slate-700 hover:border-indigo-500/50 hover:bg-slate-800'
          }
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center text-center space-y-4">
          <div className="p-4 rounded-full bg-slate-700/50 group-hover:bg-indigo-500/20 transition-colors">
            <Cloud className="h-8 w-8 text-slate-400 group-hover:text-indigo-400" />
          </div>
          <div>
            <p className="text-slate-300 font-medium">
              {isDragActive
                ? "Drop your images here..."
                : "Drop your images here or click to browse"
            }
            </p>
            <p className="text-sm text-slate-400 mt-1">
              Support for JPG, PNG, GIF, WEBP, and HEIC (max 50MB)
            </p>
          </div>
        </div>
      </div>

      {/* Selected Files List */}
      <div className="space-y-2">
        {files.map((file, index) => (
          <div
            key={index}
            className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3 border border-slate-700"
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-slate-700/50">
                <Image className="h-5 w-5 text-indigo-400"/>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-300 truncate max-w-[200px]">
                  {file.name}
                </p>
                <p className="text-xs text-slate-400">
                  {formatSize(file.size)}
                </p>
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                removeFile(index);
              }}
              className="p-1 rounded-full hover:bg-slate-700 text-slate-400 hover:text-slate-300 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}