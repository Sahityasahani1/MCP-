"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, X, ArrowRight, Loader2 } from "lucide-react";
import { getApiBaseUrl, getAuthHeaders } from "@/lib/sse-client";

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (datasetId: string, filename: string, previewInfo?: any) => void;
}

export const FileUploadModal: React.FC<FileUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    setErrorMessage(null);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMessage(null);
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (f: File) => {
    if (!f.name.toLowerCase().endsWith(".csv")) {
      setErrorMessage("Only .csv files are supported for tabular machine learning pipelines.");
      setFile(null);
      return;
    }

    // 250 MB ceiling
    if (f.size > 250 * 1024 * 1024) {
      setErrorMessage("File exceeds the 250 MB security ceiling limit.");
      setFile(null);
      return;
    }

    setFile(f);
    setUploadResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setErrorMessage(null);

    const formData = new FormData();
    formData.append("file", file);

    const apiBaseUrl = getApiBaseUrl();

    try {
      const res = await fetch(`${apiBaseUrl}/api/data/upload`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(errData.detail || "Failed to upload file.");
      }

      const data = await res.json();
      setUploadResult(data);
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred during upload.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadResult(null);
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleProceed = () => {
    if (uploadResult) {
      onUploadSuccess(uploadResult.dataset_id, uploadResult.filename, uploadResult);
      handleReset();
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="relative w-full max-w-xl bg-white border-4 border-black shadow-[10px_10px_0px_0px_#000000] p-6 text-black">
        {/* Header Bar */}
        <div className="flex items-center justify-between pb-4 mb-4 border-b-4 border-black bg-amber-300 -mx-6 -mt-6 p-4">
          <div className="flex items-center gap-2 font-mono font-black text-sm uppercase tracking-wider">
            <UploadCloud className="w-5 h-5 text-black" />
            <span>UPLOAD CSV DATASET</span>
          </div>
          <button
            onClick={() => {
              handleReset();
              onClose();
            }}
            className="p-1 font-bold text-black border-2 border-black bg-white hover:bg-black hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-4 p-3 bg-red-100 border-2 border-red-600 text-red-900 font-mono text-xs flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">UPLOAD REJECTED</p>
              <p>{errorMessage}</p>
            </div>
          </div>
        )}

        {/* State 1: Ready to Upload / Select */}
        {!uploadResult ? (
          <div>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-4 border-dashed p-8 text-center cursor-pointer transition-all ${
                isDragging
                  ? "border-black bg-amber-100 scale-[0.99]"
                  : "border-black/50 hover:border-black bg-slate-50 hover:bg-amber-50"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={handleFileChange}
              />
              <UploadCloud className="w-12 h-12 mx-auto mb-3 text-black" />
              <p className="font-mono font-black text-sm uppercase tracking-wide">
                DRAG & DROP CSV FILE HERE
              </p>
              <p className="font-mono text-xs text-slate-600 mt-1">
                or click to browse local filesystem
              </p>
              <div className="mt-3 inline-block font-mono text-[10px] bg-slate-200 border border-black px-2 py-0.5 text-slate-700">
                MAX 250 MB (.CSV)
              </div>
            </div>

            {/* Selected File Details */}
            {file && (
              <div className="mt-4 p-3 border-2 border-black bg-yellow-50 flex items-center justify-between font-mono text-xs">
                <div className="flex items-center gap-2 overflow-hidden">
                  <FileText className="w-4 h-4 shrink-0 text-black" />
                  <span className="font-bold truncate">{file.name}</span>
                  <span className="text-slate-500 shrink-0">
                    ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleReset();
                  }}
                  className="text-red-600 font-bold hover:underline shrink-0 ml-2"
                >
                  REMOVE
                </button>
              </div>
            )}

            {/* Upload Action Button */}
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => {
                  handleReset();
                  onClose();
                }}
                className="px-4 py-2 border-2 border-black font-mono font-bold text-xs uppercase hover:bg-slate-200"
              >
                CANCEL
              </button>
              <button
                type="button"
                disabled={!file || isUploading}
                onClick={handleUpload}
                className="px-6 py-2 bg-black text-white border-2 border-black font-mono font-black text-xs uppercase flex items-center gap-2 shadow-[3px_3px_0px_0px_#f59e0b] hover:shadow-none hover:translate-x-0.5 hover:translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
                    <span>UPLOADING & PARSING...</span>
                  </>
                ) : (
                  <>
                    <span>UPLOAD CSV</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          /* State 2: Upload Succeeded & Parsed */
          <div className="animate-in fade-in duration-200">
            <div className="p-4 border-2 border-black bg-emerald-50 mb-4">
              <div className="flex items-center gap-2 text-emerald-800 font-mono font-black text-sm">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <span>DATASET UPLOADED SUCCESSFULLY</span>
              </div>
              <p className="font-mono text-xs text-slate-700 mt-2">
                Saved to:{" "}
                <code className="bg-slate-200 px-1 font-bold">data/raw/{uploadResult.filename}</code>
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4 font-mono text-xs">
              <div className="p-3 border-2 border-black bg-slate-50">
                <span className="text-slate-500 block text-[10px] font-bold">DATASET ID</span>
                <span className="font-black text-black">{uploadResult.dataset_id}</span>
              </div>
              <div className="p-3 border-2 border-black bg-slate-50">
                <span className="text-slate-500 block text-[10px] font-bold">COLUMN COUNT</span>
                <span className="font-black text-black">{uploadResult.columns_count} Columns</span>
              </div>
            </div>

            {uploadResult.sample_headers && (
              <div className="mb-4 p-3 border-2 border-black bg-slate-50 font-mono text-xs">
                <span className="text-slate-500 block text-[10px] font-bold mb-1">
                  DETECTED FEATURES
                </span>
                <div className="flex flex-wrap gap-1">
                  {uploadResult.sample_headers.map((h: string, idx: number) => (
                    <span
                      key={idx}
                      className="bg-white border border-black px-1.5 py-0.5 text-[10px] font-bold"
                    >
                      {h}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between pt-2">
              <button
                type="button"
                onClick={handleReset}
                className="font-mono text-xs underline font-bold hover:text-amber-600"
              >
                Upload another file
              </button>

              <button
                type="button"
                onClick={handleProceed}
                className="px-6 py-2 bg-emerald-500 text-black border-2 border-black font-mono font-black text-xs uppercase flex items-center gap-2 shadow-[3px_3px_0px_0px_#000] hover:shadow-none hover:translate-x-0.5 hover:translate-y-0.5"
              >
                <span>CLEAN &amp; PROFILE DATASET</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
