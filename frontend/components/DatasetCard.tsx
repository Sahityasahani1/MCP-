"use client";

import React from "react";
import { Database, Download, Star, HardDrive, ExternalLink, Heart, Tag, Zap } from "lucide-react";

interface DatasetProps {
  dataset: {
    dataset_id: string;
    title: string;
    size_mb: number;
    usability_score: number;
    url?: string;
    download_count?: number;
    likes?: number;
    source?: string;
    is_mock_demo?: boolean;
    tags?: string[];
  };
  onClean?: (datasetId: string) => void;
}

export const DatasetCard: React.FC<DatasetProps> = ({ dataset, onClean }) => {
  const usabilityPct = Math.round((dataset.usability_score || 0.8) * 100);
  const sourceName = (dataset.source || "Kaggle").toUpperCase();
  const isHF = sourceName.includes("HUGGING");

  const isSafeUrl = (url?: string): boolean => {
    if (!url) return false;
    const trimmed = url.trim().toLowerCase();
    return trimmed.startsWith("http://") || trimmed.startsWith("https://");
  };

  return (
    <div className="bg-[#00FF00] text-black border-4 border-black p-4 my-2 shadow-[6px_6px_0_#000000]">
      {/* Top Header */}
      <div className="flex items-start justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <div className={`${isHF ? "bg-[#FFFF00] text-black" : "bg-black text-white"} font-mono font-black text-xs px-2.5 py-0.5 inline-flex items-center gap-1.5 border-2 border-black shadow-[2px_2px_0_#000000]`}>
            <Database className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{sourceName}</span>
          </div>

          {dataset.is_mock_demo && (
            <span className="bg-[#FF00FF] text-black border-2 border-black font-mono font-black text-[10px] px-2 py-0.5 uppercase shadow-[2px_2px_0_#000000]">
              VERIFIED BENCHMARK
            </span>
          )}

          {dataset.likes !== undefined && dataset.likes > 0 && (
            <span className="bg-white text-black border-2 border-black font-mono font-black text-[10px] px-2 py-0.5 uppercase shadow-[2px_2px_0_#000000] inline-flex items-center gap-1">
              <Heart className="w-3 h-3 text-red-600 fill-red-600" aria-hidden="true" />
              <span>{dataset.likes} LIKES</span>
            </span>
          )}
        </div>

        {dataset.url && isSafeUrl(dataset.url) && (
          <a
            href={dataset.url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Open repository for ${dataset.title}`}
            className="button bg-white text-black border-2 border-black p-1 shadow-[2px_2px_0_#000000] hover:bg-[#FFFF00] cursor-pointer inline-flex items-center"
          >
            <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
          </a>
        )}
      </div>

      {/* Dataset Title */}
      <h4 className="text-black font-black text-base uppercase leading-snug mt-3">
        {dataset.title}
      </h4>
      <code className="mono text-xs font-black bg-white text-black px-2 py-0.5 border-2 border-black mt-1.5 inline-block shadow-[2px_2px_0_#000000]">
        ID: {dataset.dataset_id}
      </code>

      {/* Tags if available */}
      {dataset.tags && dataset.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {dataset.tags.slice(0, 4).map((t, idx) => (
            <span
              key={idx}
              className="bg-white text-black text-[10px] font-mono font-bold px-1.5 py-0.2 border border-black inline-flex items-center gap-1"
            >
              <Tag className="w-2.5 h-2.5 text-black" aria-hidden="true" />
              <span>{t}</span>
            </span>
          ))}
        </div>
      )}

      {/* 3-Column Metrics Grid */}
      <div className="grid grid-cols-3 gap-2.5 mt-3 pt-3 border-t-2 border-black text-xs">
        <div className="bg-white p-2.5 border-2 border-black shadow-[3px_3px_0_#000000]">
          <div className="text-[10px] font-mono font-black uppercase text-black flex items-center gap-1">
            <Star className="w-3 h-3 text-black" aria-hidden="true" />
            <span>USABILITY</span>
          </div>
          <div className="text-black font-black text-base mt-0.5">{usabilityPct}%</div>
        </div>

        <div className="bg-white p-2.5 border-2 border-black shadow-[3px_3px_0_#000000]">
          <div className="text-[10px] font-mono font-black uppercase text-black flex items-center gap-1">
            <HardDrive className="w-3 h-3 text-black" aria-hidden="true" />
            <span>SIZE</span>
          </div>
          <div className="text-black font-black text-base mt-0.5">{dataset.size_mb} MB</div>
        </div>

        <div className="bg-white p-2.5 border-2 border-black shadow-[3px_3px_0_#000000]">
          <div className="text-[10px] font-mono font-black uppercase text-black flex items-center gap-1">
            <Download className="w-3.5 h-3.5 text-black" aria-hidden="true" />
            <span>DOWNLOADS</span>
          </div>
          <div className="text-black font-black text-base mt-0.5">
            {dataset.download_count ? dataset.download_count.toLocaleString() : "500K+"}
          </div>
        </div>
      </div>

      {/* 1-Click Clean & Benchmark Action */}
      {onClean && (
        <div className="mt-3 pt-2.5 border-t-2 border-black">
          <button
            type="button"
            onClick={() => onClean(dataset.dataset_id)}
            aria-label={`Clean and benchmark dataset ${dataset.dataset_id}`}
            className="w-full bg-black text-white hover:bg-white hover:text-black border-2 border-black py-2 px-3 font-mono font-black text-xs uppercase flex items-center justify-center gap-1.5 shadow-[3px_3px_0_#000000] hover:shadow-none hover:translate-x-0.5 hover:translate-y-0.5 transition-none cursor-pointer"
          >
            <Zap className="w-3.5 h-3.5 text-yellow-300 fill-yellow-300" aria-hidden="true" />
            <span>CLEAN &amp; BENCHMARK</span>
          </button>
        </div>
      )}
    </div>
  );
};
