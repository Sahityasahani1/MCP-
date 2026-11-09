"use client";

import React from "react";
import { ShieldAlert, CheckCircle2, XCircle, Terminal, Cpu } from "lucide-react";

interface ApprovalPromptProps {
  data: {
    dataset_id: string;
    approval_token: string;
    cleaning_recipe: {
      handle_missing: string;
      drop_duplicates: boolean;
      normalize_headers: boolean;
      export_formats: string[];
    };
  };
  onApprove: (token: string) => void;
  onReject?: () => void;
  isLoading?: boolean;
}

export const ApprovalPrompt: React.FC<ApprovalPromptProps> = ({
  data,
  onApprove,
  onReject,
  isLoading,
}) => {
  return (
    <div className="bg-[#FF0000] text-black border-4 border-black p-5 md:p-6 my-4 shadow-[8px_8px_0_#000000]">
      {/* Brutalist Warning Header */}
      <div className="flex items-center gap-2 bg-black text-white px-3 py-1.5 font-mono font-black text-xs md:text-sm border-2 border-black shadow-[3px_3px_0_#000000] uppercase inline-flex">
        <ShieldAlert className="w-5 h-5 text-[#FFFF00]" aria-hidden="true" />
        <span>HUMAN-IN-THE-LOOP (HITL) SECURITY GATE</span>
      </div>

      <p className="text-sm font-black text-black uppercase mt-3 leading-snug">
        TARGET PIPELINE PROPOSAL REQUIRES AUTHORIZATION BEFORE EXECUTING DISK OPERATIONS:
      </p>

      {/* Cleaning Recipe Spec */}
      <div className="bg-white text-black p-4 border-3 border-black my-3 text-xs font-mono font-bold shadow-[4px_4px_0_#000000] space-y-1.5">
        <div className="text-black font-black uppercase flex items-center gap-1.5 border-b-2 border-black pb-1 mb-2">
          <Terminal className="w-4 h-4" aria-hidden="true" />
          <span>TARGET DATASET: {data.dataset_id}</span>
        </div>
        <div>
          • MISSING VALUES: <span className="bg-[#FFFF00] px-1 border border-black">{data.cleaning_recipe?.handle_missing || "median_impute"}</span>
        </div>
        <div>
          • DUPLICATES STRIP: <span className="bg-[#FFFF00] px-1 border border-black">{data.cleaning_recipe?.drop_duplicates ? "ENABLED (DROP)" : "KEEP"}</span>
        </div>
        <div>
          • HEADER NORMALIZATION: <span className="bg-[#FFFF00] px-1 border border-black">SNAKE_CASE</span>
        </div>
        <div>
          • OUTLIER TREATMENT: <span className="bg-[#FFFF00] px-1 border border-black">WINSORIZATION &amp; IQR CAPPING</span>
        </div>
        <div>
          • ML PARTITIONING: <span className="bg-[#FFFF00] px-1 border border-black">80/20 STRATIFIED (ZERO DATA LEAKAGE)</span>
        </div>
        <div>
          • BASELINE AUTOML: <span className="bg-[#FFFF00] px-1 border border-black">LIGHTGBM CLASSIFIER / ROC-AUC</span>
        </div>
        <div>
          • EXPORT FORMATS: <span className="bg-[#00FF00] text-black px-1 border border-black font-black">CSV + FULL PARQUET + TRAIN/TEST PARQUET</span>
        </div>
        <div className="pt-1 text-[11px] text-black">
          • SINGLE-USE TOKEN: <span className="font-mono bg-black text-white px-1.5 py-0.5">{data.approval_token}</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center gap-3 mt-4">
        <button
          onClick={() => onApprove(data.approval_token)}
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
