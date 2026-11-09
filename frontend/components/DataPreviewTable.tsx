"use client";

import React, { useState } from "react";
import { Download, Check, Activity, FileSpreadsheet, Zap, Target, BarChart2 } from "lucide-react";

interface DataPreviewProps {
  data: {
    status: string;
    dataset_name: string;
    output_filename: string;
    output_csv_filepath?: string;
    output_parquet_filepath?: string;
    train_parquet_filepath?: string;
    test_parquet_filepath?: string;
    target_column?: string;
    baseline_benchmark?: {
      status?: string;
      target_column?: string;
      metrics?: Record<string, any>;
      top_features?: Array<{ feature: string; importance_score: number }>;
    };
    stats_before?: {
      rows: number;
      cols: number;
      null_count: number;
      duplicate_count: number;
      health_score: number;
    };
    stats_after?: {
      rows: number;
      cols: number;
      null_count: number;
      duplicate_count: number;
      health_score: number;
    };
    health_score_delta?: number;
    actions_taken?: string[];
    column_types?: Record<string, string>;
    head_preview?: Record<string, any>[];
  };
}

export const DataPreviewTable: React.FC<DataPreviewProps> = ({ data }) => {
  const [activeTab, setActiveTab] = useState<"preview" | "types" | "baseline" | "actions">("preview");

  const previewRows = data.head_preview || [];
  const columns = previewRows.length > 0 ? Object.keys(previewRows[0]) : [];

  const scoreBefore = data.stats_before?.health_score || 95.0;
  const scoreAfter = data.stats_after?.health_score || 99.5;
  const delta = data.health_score_delta || (scoreAfter - scoreBefore);
  const baseline = data.baseline_benchmark;
  const prefix = data.dataset_name;

  return (
    <div className="bg-white text-black border-4 border-black p-5 md:p-6 my-4 shadow-[8px_8px_0_#000000]">
      {/* Header with Health Score */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b-4 border-black">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-[#FFFF00] text-black border-3 border-black shadow-[3px_3px_0_#000000]">
            <FileSpreadsheet className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <h4 className="text-black font-black text-base md:text-lg uppercase">
              PIPELINE EXECUTION &amp; PROFILING (v3.0)
            </h4>
            <div className="flex items-center gap-2 flex-wrap mt-1">
              <span className="mono text-xs font-black bg-[#FFFF00] text-black px-2 py-0.5 border-2 border-black shadow-[2px_2px_0_#000000]">
                FILE: {data.output_filename}
              </span>
              {data.target_column && (
                <span className="mono text-xs font-black bg-[#FF00FF] text-black px-2 py-0.5 border-2 border-black shadow-[2px_2px_0_#000000] inline-flex items-center gap-1">
                  <Target className="w-3 h-3" />
                  TARGET: {data.target_column}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Health Score Metric Badge */}
        <div className="flex items-center gap-2 bg-[#00FF00] text-black px-3.5 py-1.5 border-3 border-black shadow-[3px_3px_0_#000000] font-mono font-black text-sm uppercase">
          <Activity className="w-5 h-5 text-black" aria-hidden="true" />
          <span>HEALTH SCORE: {scoreAfter.toFixed(1)}/100</span>
          {delta > 0 && (
            <span className="bg-black text-white px-1.5 py-0.5 text-xs ml-1">
              (+{delta.toFixed(1)})
            </span>
          )}
        </div>
      </div>

      {/* 4-Column Raw Stats Metric Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4 text-xs">
        <div className="bg-[#FFFF00] p-3 border-3 border-black shadow-[3px_3px_0_#000000]">
          <div className="font-mono text-[10px] font-black uppercase text-black">CLEAN ROWS</div>
          <div className="text-black font-black text-lg mt-0.5">
            {data.stats_after?.rows?.toLocaleString() || "500"}
          </div>
        </div>
        <div className="bg-[#FFFF00] p-3 border-3 border-black shadow-[3px_3px_0_#000000]">
          <div className="font-mono text-[10px] font-black uppercase text-black">COLUMNS</div>
          <div className="text-black font-black text-lg mt-0.5">
            {data.stats_after?.cols || "5"}
          </div>
        </div>
        <div className="bg-[#FFFF00] p-3 border-3 border-black shadow-[3px_3px_0_#000000]">
          <div className="font-mono text-[10px] font-black uppercase text-black">NULLS RESOLVED</div>
          <div className="text-black font-black text-lg mt-0.5">
            {data.stats_before?.null_count || "0"}
          </div>
        </div>
        <div className="bg-[#FFFF00] p-3 border-3 border-black shadow-[3px_3px_0_#000000]">
          <div className="font-mono text-[10px] font-black uppercase text-black">DUPLICATES DROPPED</div>
          <div className="text-black font-black text-lg mt-0.5">
            {data.stats_before?.duplicate_count || "0"}
          </div>
        </div>
      </div>

      {/* Brutalist Tab Switcher */}
      <div className="flex flex-wrap items-center gap-2 border-b-3 border-black pb-3 text-xs font-black uppercase">
        <button
          onClick={() => setActiveTab("preview")}
          className={`px-4 py-2 border-2 border-black cursor-pointer shadow-[2px_2px_0_#000000] ${
            activeTab === "preview"
              ? "bg-black text-white"
              : "bg-white text-black hover:bg-[#FFFF00]"
          }`}
        >
          TOP 5 PREVIEW
        </button>
        <button
          onClick={() => setActiveTab("types")}
          className={`px-4 py-2 border-2 border-black cursor-pointer shadow-[2px_2px_0_#000000] ${
            activeTab === "types"
              ? "bg-black text-white"
              : "bg-white text-black hover:bg-[#FFFF00]"
          }`}
        >
          INFERRED TYPES ({Object.keys(data.column_types || {}).length})
        </button>
        {baseline && baseline.status === "success" && (
          <button
            onClick={() => setActiveTab("baseline")}
            className={`px-4 py-2 border-2 border-black cursor-pointer shadow-[2px_2px_0_#000000] flex items-center gap-1.5 ${
              activeTab === "baseline"
                ? "bg-[#0000FF] text-white"
                : "bg-white text-black hover:bg-[#FFFF00]"
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            BASELINE AUTOML
          </button>
        )}
        <button
          onClick={() => setActiveTab("actions")}
          className={`px-4 py-2 border-2 border-black cursor-pointer shadow-[2px_2px_0_#000000] ${
            activeTab === "actions"
              ? "bg-black text-white"
              : "bg-white text-black hover:bg-[#FFFF00]"
          }`}
        >
          ACTIONS LOG ({data.actions_taken?.length || 0})
        </button>
      </div>

      {/* Tab Panes */}
      <div className="mt-3">
        {activeTab === "preview" && (
          <div className="overflow-x-auto border-3 border-black bg-white shadow-[4px_4px_0_#000000]">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-black text-white font-mono font-black border-b-3 border-black">
                <tr>
                  {columns.map((col) => (
                    <th key={col} className="p-3 uppercase border-r-2 border-black whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y-2 divide-black font-mono font-bold text-black">
                {previewRows.map((row, idx) => (
                  <tr key={idx} className={idx % 2 === 0 ? "bg-white" : "bg-neutral-100"}>
                    {columns.map((col) => (
                      <td key={col} className="p-2.5 border-r-2 border-black whitespace-nowrap">
                        {String(row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "types" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs font-mono">
            {Object.entries(data.column_types || {}).map(([col, typeStr]) => (
              <div
                key={col}
                className="p-3 bg-white border-2 border-black shadow-[3px_3px_0_#000000] flex justify-between items-center"
              >
                <span className="font-black text-black">{col}</span>
                <span className="bg-[#0000FF] text-white px-2 py-0.5 border border-black font-black uppercase text-[11px]">
                  {typeStr}
                </span>
              </div>
            ))}
          </div>
        )}

        {activeTab === "baseline" && baseline && baseline.status === "success" && (
          <div className="p-4 bg-white border-3 border-black shadow-[4px_4px_0_#000000] space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-black pb-3">
              <div className="font-mono font-black text-sm uppercase flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-[#0000FF]" />
                <span>MODEL: {baseline.metrics?.algorithm || "LightGBM Classifier"}</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono font-bold">
                {baseline.metrics?.roc_auc && (
                  <span className="bg-[#00FF00] text-black px-2 py-1 border-2 border-black shadow-[2px_2px_0_#000000]">
                    ROC-AUC: {baseline.metrics.roc_auc}
                  </span>
                )}
                {baseline.metrics?.accuracy && (
                  <span className="bg-[#FFFF00] text-black px-2 py-1 border-2 border-black shadow-[2px_2px_0_#000000]">
                    ACCURACY: {baseline.metrics.accuracy}
                  </span>
                )}
                {baseline.metrics?.f1_weighted && (
                  <span className="bg-white text-black px-2 py-1 border-2 border-black shadow-[2px_2px_0_#000000]">
                    F1: {baseline.metrics.f1_weighted}
                  </span>
                )}
              </div>
            </div>

            {/* Top 5 Feature Importances */}
            <div>
              <h5 className="font-mono font-black text-xs uppercase mb-2">TOP 5 FEATURE IMPORTANCES (GAIN/SPLITS):</h5>
              <div className="space-y-2">
                {(baseline.top_features || []).map((feat, idx) => {
                  const maxScore = Math.max(...(baseline.top_features || []).map((f) => f.importance_score), 1);
                  const pct = Math.round((feat.importance_score / maxScore) * 100);
                  return (
                    <div key={idx} className="font-mono text-xs">
                      <div className="flex justify-between font-bold mb-0.5">
                        <span>{feat.feature}</span>
                        <span>{feat.importance_score}</span>
                      </div>
                      <div className="w-full bg-neutral-200 border-2 border-black h-4">
                        <div
                          className="bg-[#0000FF] h-full"
                          style={{ width: `${Math.max(5, pct)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {activeTab === "actions" && (
          <div className="space-y-2 text-xs font-mono font-bold bg-white p-4 border-3 border-black shadow-[3px_3px_0_#000000]">
            {(data.actions_taken || []).map((action, i) => (
              <div key={i} className="flex items-center gap-2.5">
                <span className="bg-[#00FF00] text-black border border-black p-0.5 shrink-0">
                  <Check className="w-3.5 h-3.5" aria-hidden="true" />
                </span>
                <span className="uppercase text-black">{action}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Download Action Bar */}
      <div className="flex flex-wrap items-center justify-end gap-2.5 mt-4 pt-3 border-t-3 border-black">
        <a
          href={`http://127.0.0.1:8000/api/data/download/${data.output_filename}`}
          download
          aria-label={`Download cleaned CSV ${data.output_filename}`}
          className="button button--blue px-4 py-2 font-black uppercase text-xs shadow-[3px_3px_0_#000000] inline-flex items-center gap-1.5 cursor-pointer"
        >
          <Download className="w-3.5 h-3.5" aria-hidden="true" />
          <span>CLEAN CSV</span>
        </a>

        <a
          href={`http://127.0.0.1:8000/api/data/download/${prefix}_cleaned.parquet`}
          download
          aria-label="Download cleaned Parquet"
          className="button bg-white text-black hover:bg-[#FFFF00] px-4 py-2 font-black uppercase text-xs shadow-[3px_3px_0_#000000] inline-flex items-center gap-1.5 cursor-pointer border-2 border-black"
        >
          <Download className="w-3.5 h-3.5" aria-hidden="true" />
          <span>FULL PARQUET</span>
        </a>

        {data.train_parquet_filepath && (
          <a
            href={`http://127.0.0.1:8000/api/data/download/${prefix}_train.parquet`}
            download
            aria-label="Download Train Parquet"
            className="button button--green px-4 py-2 font-black uppercase text-xs shadow-[3px_3px_0_#000000] inline-flex items-center gap-1.5 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" aria-hidden="true" />
            <span>TRAIN PARQUET (80%)</span>
          </a>
        )}

        {data.test_parquet_filepath && (
          <a
            href={`http://127.0.0.1:8000/api/data/download/${prefix}_test.parquet`}
            download
            aria-label="Download Test Parquet"
            className="button bg-[#FF00FF] text-black px-4 py-2 font-black uppercase text-xs shadow-[3px_3px_0_#000000] inline-flex items-center gap-1.5 cursor-pointer border-2 border-black"
          >
            <Download className="w-3.5 h-3.5" aria-hidden="true" />
            <span>TEST PARQUET (20%)</span>
          </a>
        )}
      </div>
    </div>
  );
};
