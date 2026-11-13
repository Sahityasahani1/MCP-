"use client";

import React, { useState } from "react";
import { ShieldAlert, CheckCircle2, XCircle, Terminal, Cpu, SlidersHorizontal, ChevronDown, ChevronUp } from "lucide-react";

interface ApprovalPromptProps {
  data: {
    dataset_id: string;
    approval_token: string;
    cleaning_recipe: {
      handle_missing: string;
      drop_duplicates: boolean;
      normalize_headers: boolean;
      export_formats: string[];
      test_size?: number;
      target_column?: string;
      cap_outliers?: boolean;
    };
  };
  onApprove: (token: string, customRecipe?: any) => void;
  onReject?: () => void;
  isLoading?: boolean;
}

export const ApprovalPrompt: React.FC<ApprovalPromptProps> = ({
  data,
  onApprove,
  onReject,
  isLoading,
}) => {
  const [showCustomizer, setShowCustomizer] = useState(false);
  const [handleMissing, setHandleMissing] = useState<string>(
    data.cleaning_recipe?.handle_missing || "median_impute"
  );
  const [dropDuplicates, setDropDuplicates] = useState<boolean>(
    data.cleaning_recipe?.drop_duplicates !== false
  );
  const [normalizeHeaders, setNormalizeHeaders] = useState<boolean>(
    data.cleaning_recipe?.normalize_headers !== false
  );
  const [capOutliers, setCapOutliers] = useState<boolean>(
    data.cleaning_recipe?.cap_outliers !== false
  );
  const [testSize, setTestSize] = useState<number>(
    data.cleaning_recipe?.test_size || 0.2
  );
  const [targetColumn, setTargetColumn] = useState<string>(
    data.cleaning_recipe?.target_column || ""
  );

  const handleApproveClick = () => {
    const customRecipe = {
      handle_missing: handleMissing,
      drop_duplicates: dropDuplicates,
      normalize_headers: normalizeHeaders,
      cap_outliers: capOutliers,
      test_size: Number(testSize),
      target_column: targetColumn.trim() ? targetColumn.trim() : null,
    };
    onApprove(data.approval_token, customRecipe);
  };

  return (
    <div className="bg-[#FF0000] text-black border-4 border-black p-5 md:p-6 my-4 shadow-[8px_8px_0_#000000]">
      {/* Warning Header */}
      <div className="flex items-center justify-between bg-black text-white px-3 py-1.5 font-mono font-black text-xs md:text-sm border-2 border-black shadow-[3px_3px_0_#000000] uppercase">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-[#FFFF00]" aria-hidden="true" />
          <span>PIPELINE AUTHORIZATION</span>
        </div>
        <span className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 font-mono">
          TOKEN: {data.approval_token.substring(0, 16)}
        </span>
      </div>

      <div className="flex items-center gap-2 my-2.5 text-xs font-mono font-black text-black">
        <Terminal className="w-4 h-4 shrink-0" aria-hidden="true" />
        <span>DATASET:</span>
        <span className="bg-white px-1.5 py-0.5 border border-black">{data.dataset_id}</span>
      </div>

      {/* Recipe Overview Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 my-2.5 text-xs font-mono">
        <div className="p-2 bg-white border-2 border-black shadow-[2px_2px_0_#000000]">
          <span className="block text-slate-500 text-[10px] font-black uppercase">PARTITION</span>
          <span className="font-black text-black">
            {Math.round((1 - testSize) * 100)}/{Math.round(testSize * 100)} Train/Test
          </span>
        </div>
        <div className="p-2 bg-white border-2 border-black shadow-[2px_2px_0_#000000]">
          <span className="block text-slate-500 text-[10px] font-black uppercase">IMPUTATION</span>
          <span className="font-black text-black uppercase">
            {handleMissing.replace("_impute", "")}
          </span>
        </div>
        <div className="p-2 bg-white border-2 border-black shadow-[2px_2px_0_#000000]">
          <span className="block text-slate-500 text-[10px] font-black uppercase">OUTLIERS</span>
          <span className="font-black text-black">
            {capOutliers ? "Winsorize (IQR)" : "Untouched"}
          </span>
        </div>
        <div className="p-2 bg-white border-2 border-black shadow-[2px_2px_0_#000000]">
          <span className="block text-slate-500 text-[10px] font-black uppercase">TARGET</span>
          <span className="font-black text-black truncate block">
            {targetColumn.trim() || "Auto-detect"}
          </span>
        </div>
      </div>

      {/* Collapsible Recipe Customizer Toggle */}
      <div className="my-3">
        <button
          type="button"
          onClick={() => setShowCustomizer(!showCustomizer)}
          className="w-full bg-amber-300 text-black border-2 border-black px-3 py-2 font-mono font-black text-xs uppercase flex items-center justify-between hover:bg-amber-400 shadow-[3px_3px_0_#000000] transition-colors"
        >
          <span className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4" />
            {showCustomizer ? "COLLAPSE RECIPE CUSTOMIZER" : "CUSTOMIZE PIPELINE RECIPE & SPLITS"}
          </span>
          {showCustomizer ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showCustomizer && (
          <div className="bg-slate-100 border-3 border-black p-4 mt-2 shadow-[4px_4px_0_#000000] font-mono text-xs space-y-3 animate-in fade-in duration-150">
            {/* Missing Value Strategy */}
            <div>
              <label className="block font-black text-black mb-1">
                MISSING VALUE IMPUTATION STRATEGY:
              </label>
              <select
                value={handleMissing}
                onChange={(e) => setHandleMissing(e.target.value)}
                className="w-full bg-white border-2 border-black p-2 font-bold font-mono text-xs focus:ring-2 focus:ring-black outline-none"
              >
                <option value="median_impute">Median Imputation (Recommended for skewed numeric data)</option>
                <option value="mean_impute">Mean Imputation (Standard Gaussian distribution)</option>
                <option value="mode_impute">Mode Imputation (Most frequent value for categorical)</option>
                <option value="drop">Drop Rows with Any Null Values</option>
              </select>
            </div>

            {/* Train / Test Split Slider */}
            <div>
              <div className="flex justify-between font-black text-black mb-1">
                <span>TRAIN / TEST SPLIT RATIO:</span>
                <span className="bg-black text-white px-1.5 py-0.5">
                  {Math.round((1 - testSize) * 100)}% TRAIN / {Math.round(testSize * 100)}% TEST
                </span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.40"
                step="0.05"
                value={testSize}
                onChange={(e) => setTestSize(parseFloat(e.target.value))}
                className="w-full accent-black cursor-pointer h-2 bg-slate-300 border border-black"
              />
              <div className="flex justify-between text-[10px] text-slate-600 font-bold mt-0.5">
                <span>90/10 (Max Train Data)</span>
                <span>80/20 (Industry Standard)</span>
                <span>60/40 (Heavy Validation)</span>
              </div>
            </div>

            {/* Target Column Override */}
            <div>
              <label className="block font-black text-black mb-1">
                TARGET FEATURE OVERRIDE (OPTIONAL):
              </label>
              <input
                type="text"
                placeholder="Leave blank to auto-detect target column..."
                value={targetColumn}
                onChange={(e) => setTargetColumn(e.target.value)}
                className="w-full bg-white border-2 border-black p-2 font-mono text-xs font-bold outline-none placeholder:text-slate-400"
              />
            </div>

            {/* Toggle Checkboxes */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 border-t-2 border-black/20">
              <label className="flex items-center gap-2 cursor-pointer font-bold">
                <input
                  type="checkbox"
                  checked={capOutliers}
                  onChange={(e) => setCapOutliers(e.target.checked)}
                  className="w-4 h-4 accent-black border-2 border-black cursor-pointer"
                />
                <span>Winsorize Extreme Outliers (IQR)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer font-bold">
                <input
                  type="checkbox"
                  checked={dropDuplicates}
                  onChange={(e) => setDropDuplicates(e.target.checked)}
                  className="w-4 h-4 accent-black border-2 border-black cursor-pointer"
                />
                <span>Drop Identical Duplicate Rows</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer font-bold">
                <input
                  type="checkbox"
                  checked={normalizeHeaders}
                  onChange={(e) => setNormalizeHeaders(e.target.checked)}
                  className="w-4 h-4 accent-black border-2 border-black cursor-pointer"
                />
                <span>Normalize Headers (snake_case)</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center gap-3 mt-4">
        <button
          onClick={handleApproveClick}
          disabled={isLoading}
          aria-label="Approve and execute pipeline"
          className="button button--green w-full sm:flex-1 py-3 text-sm font-black uppercase shadow-[4px_4px_0_#000000] inline-flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <Cpu className="w-4 h-4 animate-spin" aria-hidden="true" />
              <span>EXECUTING LOCAL PIPELINE...</span>
            </>
          ) : (
            <>
              <CheckCircle2 className="w-5 h-5" aria-hidden="true" />
              <span>APPROVE &amp; EXECUTE PIPELINE</span>
            </>
          )}
        </button>

        {onReject && (
          <button
            onClick={onReject}
            disabled={isLoading}
            aria-label="Reject and cancel pipeline execution"
            className="button bg-white text-black hover:bg-black hover:text-white w-full sm:w-auto py-3 px-5 text-sm font-black uppercase shadow-[4px_4px_0_#000000] cursor-pointer"
          >
            <XCircle className="w-4 h-4 inline mr-1.5" aria-hidden="true" />
            ABORT
          </button>
        )}
      </div>
    </div>
  );
};
