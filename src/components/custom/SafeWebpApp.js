// src/components/custom/SafeWebpApp.js
"use client";
import React, { useState, useCallback, useEffect } from "react";
import axios from 'axios';
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import {
  Bolt,
  Image as ImageIcon,
  Upload,
  Sparkles,
  Download,
} from "lucide-react";
import { apiService } from "@/services/api";
import StatsGrid from "./StatsGrid";
import FileUpload from "./FileUpload";

export default function SafeWebpApp() {
  const [quality, setQuality] = useState(80);
  const [preserveMetadata, setPreserveMetadata] = useState(true);
  const [smartOptimize, setSmartOptimize] = useState(true);
  const [progress, setProgress] = useState(0);
  const [isConverting, setIsConverting] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [convertedFiles, setConvertedFiles] = useState([]);
  const [stats, setStats] = useState({
    totalFiles: 0,
    totalSize: "0 MB",
    optimizedSize: "0 MB",
    reduction: "0%",
  });

  const handleDownload = async (fileUrl) => {
    try {
      const response = await axios({
        url: fileUrl,
        method: 'GET',
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileUrl.split("/").pop());
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
  };

  const handleConversion = useCallback(async () => {
    if (selectedFiles.length === 0) return;

    setIsConverting(true);
    setProgress(0);
    setConvertedFiles([]);

    try {
      const settings = {
        quality,
        preserve_metadata: preserveMetadata,
        smart_optimize: smartOptimize,
      };

      const response = await apiService.convertImages(
        selectedFiles,
        settings,
        (progressData) => {
          setProgress(progressData.progress || 0);

          if (progressData.total_saved) {
            setStats((prev) => ({
              ...prev,
              optimizedSize: formatFileSize(progressData.total_saved),
              reduction: `${progressData.average_reduction?.toFixed(1) || 0}%`,
            }));
          }
        }
      );

      setConvertedFiles(response.files || []);
      setIsConverting(false);
    } catch (error) {
      console.error("Conversion error:", error);
      setIsConverting(false);
    }
  }, [selectedFiles, quality, preserveMetadata, smartOptimize]);

  const formatFileSize = (bytes) => {
    const units = ["B", "KB", "MB", "GB"];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`;
  };

  useEffect(() => {
    return () => {
      apiService.closeWebSocket();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="max-w-6xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <Bolt className="h-12 w-12 text-indigo-500" />
            <Sparkles className="h-8 w-8 text-indigo-300 -ml-4" />
          </div>
          <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400 mb-4">
            SafeWebp Pro
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Experience lightning-fast image optimization powered by AI. Convert
            and compress your images without losing quality.
          </p>
        </div>
        {/* Stats Section */}
        <div className="mb-8">
          <StatsGrid stats={stats} />
        </div>
        {/* Converted Files Section */}

        {convertedFiles.length > 0 && (
          <div className="mb-8">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="border-b border-slate-700">
                <CardTitle className="flex items-center gap-2">
                  <Download className="h-5 w-5 text-indigo-400" />
                  Converted Files
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="space-y-4">
                  {convertedFiles.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg"
                    >
                      <div className="flex items-center space-x-4">
                        <ImageIcon className="h-5 w-5 text-indigo-400" />
                        <div>
                          <p className="text-sm font-medium text-slate-300">
                            {file.output_path.split("/").pop()}
                          </p>
                          <div className="flex items-center gap-2 text-xs text-slate-400">
                            <span>
                              Original: {formatFileSize(file.original_size)}
                            </span>
                            <span>→</span>
                            <span>
                              New: {formatFileSize(file.converted_size)}
                            </span>
                            <span className="text-emerald-400">
                              ({file.reduction_percent.toFixed(1)}% smaller)
                            </span>
                          </div>
                        </div>
                      </div>
                      <Button
                        onClick={() => handleDownload(file.output_path)}
                        className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 rounded-md text-sm font-medium transition-colors"
                      >
                        Download
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        {/* Main Content */}
        <div className="grid gap-8 md:grid-cols-2">
          {/* Left Column */}
          <div className="space-y-8">
            {/* Upload Card */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="border-b border-slate-700">
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5 text-indigo-400" />
                  Upload Images
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <FileUpload
                  selectedFiles={selectedFiles}
                  onFilesSelected={setSelectedFiles}
                  onStatsUpdate={setStats}
                />
              </CardContent>
            </Card>

            {/* Settings Card */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="border-b border-slate-700">
                <CardTitle className="flex items-center gap-2">
                  <ImageIcon className="h-5 w-5 text-indigo-400" />
                  Optimization Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Quality: {quality}%
                    </label>
                    <div className="relative">
                      <Slider
                        value={[quality]}
                        onValueChange={([value]) => setQuality(value)}
                        max={100}
                        step={1}
                        className="relative flex items-center select-none touch-none w-full transition-colors bg-slate-700 h-2 rounded-full cursor-pointer"
                      />
                      <style jsx global>{`
                        .text-slate-300 + div [data-orientation="horizontal"] {
                          height: 3px;
                          background: rgb(51, 65, 85);
                        }
                        [role="slider"] {
                          background: rgb(99, 102, 241) !important;
                          border: none !important;
                          height: 16px !important;
                          width: 16px !important;
                        }
                        [data-orientation="horizontal"] > div {
                          background: rgb(99, 102, 241);
                        }
                      `}</style>
                    </div>
                  </div>

                  <div className="space-y-4 pt-4 border-t border-slate-700">
                    <div className="flex items-center space-x-3">
                      <Checkbox
                        id="preserve-metadata"
                        checked={preserveMetadata}
                        onCheckedChange={setPreserveMetadata}
                        className="border-slate-600 data-[state=checked]:bg-indigo-500"
                      />
                      <label
                        htmlFor="preserve-metadata"
                        className="text-sm text-slate-300"
                      >
                        Preserve Metadata
                      </label>
                    </div>

                    <div className="flex items-center space-x-3">
                      <Checkbox
                        id="smart-optimize"
                        checked={smartOptimize}
                        onCheckedChange={setSmartOptimize}
                        className="border-slate-600 data-[state=checked]:bg-indigo-500"
                      />
                      <label
                        htmlFor="smart-optimize"
                        className="text-sm text-slate-300"
                      >
                        Smart Optimization
                      </label>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column */}
          <div className="space-y-8">
            {/* Progress Card */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="pt-6">
                <div className="space-y-4">
                  <Progress value={progress} className="h-2 bg-slate-700" />
                  <div className="text-center">
                    <p className="text-lg font-semibold text-slate-300">
                      {isConverting ? "Converting..." : "Ready"}
                    </p>
                    <p className="text-sm text-slate-400 mt-1">
                      {isConverting
                        ? `Processing ${selectedFiles.length} files...`
                        : "Select files to begin conversion"}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="grid grid-cols-2 gap-4">
              <Button
                onClick={handleConversion}
                disabled={isConverting || selectedFiles.length === 0}
                className="bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white shadow-lg shadow-indigo-500/25 p-5"
              >
                Start Conversion
              </Button>
              <Button
                onClick={() => {
                  setIsConverting(false);
                  apiService.closeWebSocket();
                }}
                disabled={!isConverting}
                variant="destructive"
                className="bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/25 p-5"
              >
                Stop Conversion
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}