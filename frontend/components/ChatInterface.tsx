"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Brain, Cpu, Database, ShieldCheck, DollarSign, RefreshCw } from "lucide-react";
import { consumeSSEStream } from "../lib/sse-client";
import { PaperCard } from "./PaperCard";
import { DatasetCard } from "./DatasetCard";
import { ApprovalPrompt } from "./ApprovalPrompt";
import { DataPreviewTable } from "./DataPreviewTable";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content?: string;
  thoughts?: string[];
  papers?: any[];
  datasets?: any[];
  approvalRequest?: any;
  pipelineResult?: any;
  costAudit?: any;
}

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "WELCOME TO AMRA // AUTONOMOUS ML RESEARCH AGENT [MULTI-SOURCE ENGINE].\n\nENTER A RESEARCH HYPOTHESIS BELOW (E.G., 'FIND HIGH-CITATION PAPERS ON GNN FOR FRAUD DETECTION AND SOURCED DATASETS').\n\nI SEARCH VERIFIED LITERATURE ACROSS ARXIV & OPENALEX (250M+ WORKS WITH CITATION METRICS & OA PDFS), SOURCE TABULAR BENCHMARKS ACROSS KAGGLE & HUGGING FACE, AND EXECUTE DETERMINISTIC DATA CLEANING WITH EXPLICIT HITL AUTHORIZATION.",
    },
  ]);
  const [input, setInput] = useState("");
  const [provider, setProvider] = useState<"gemini" | "groq" | "ollama">("gemini");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentThought, setCurrentThought] = useState<string | null>(null);
  const [sessionId] = useState(() => `sess_${Math.random().toString(36).substring(2, 10)}`);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "auto" });
  }, [messages, currentThought]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userText = input.trim();
    setInput("");

    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `asst_${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: userText },
      { id: assistantMsgId, role: "assistant", thoughts: [], papers: [], datasets: [] },
    ]);

    setIsStreaming(true);
    setCurrentThought("INITIALIZING REASONING LOOP...");

    await consumeSSEStream(
      "http://127.0.0.1:8000/api/chat/stream",
      { message: userText, session_id: sessionId, provider },
      {
        onThought: (thought) => {
          setCurrentThought(thought.toUpperCase());
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId ? { ...m, thoughts: [...(m.thoughts || []), thought] } : m
            )
          );
        },
        onToolResult: (tool, result) => {
          if (tool === "search_academic_papers" || tool === "search_openalex_papers") {
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantMsgId ? { ...m, papers: result } : m))
            );
          } else if (tool === "find_kaggle_datasets" || tool === "find_huggingface_datasets") {
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantMsgId ? { ...m, datasets: result } : m))
            );
          } else if (tool === "trigger_data_pipeline") {
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantMsgId ? { ...m, pipelineResult: result } : m))
            );
          }
        },
        onHITLRequired: (data) => {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantMsgId ? { ...m, approvalRequest: data } : m))
          );
        },
        onTextDelta: (content) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId ? { ...m, content: (m.content || "") + content } : m
            )
          );
        },
        onCostAudit: (audit) => {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantMsgId ? { ...m, costAudit: audit } : m))
          );
        },
        onComplete: () => {
          setIsStreaming(false);
          setCurrentThought(null);
        },
        onError: (err) => {
          setIsStreaming(false);
          setCurrentThought(null);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? { ...m, content: `CRITICAL EXECUTION ERROR: ${err}` }
                : m
            )
          );
        },
      }
    );
  };

  const handleApprovePipeline = async (token: string, messageId: string) => {
    setIsStreaming(true);
    setCurrentThought("EXECUTING HITL DATA CLEANING PIPELINE...");

    await consumeSSEStream(
      "http://127.0.0.1:8000/api/chat/approve",
      { approval_token: token, session_id: sessionId },
      {
        onThought: (t) => setCurrentThought(t.toUpperCase()),
        onToolResult: (tool, result) => {
          if (tool === "trigger_data_pipeline") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === messageId
                  ? { ...m, approvalRequest: null, pipelineResult: result }
                  : m
              )
            );
          }
        },
        onTextDelta: (text) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === messageId ? { ...m, content: (m.content || "") + "\n\n" + text } : m
            )
          );
        },
        onComplete: () => {
          setIsStreaming(false);
          setCurrentThought(null);
        },
        onError: (err) => {
          setIsStreaming(false);
          setCurrentThought(null);
        },
      }
    );
  };

  return (
    <div className="flex flex-col h-screen max-w-6xl mx-auto p-4 md:p-6 bg-white text-black font-sans">
      {/* Brutalist Top Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b-4 border-black gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-[#FFFF00] text-black border-4 border-black shadow-[4px_4px_0_#000000]">
            <Brain className="w-7 h-7" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-black uppercase tracking-tight text-black flex items-center gap-2">
              AMRA // RESEARCH AGENT
              <span className="font-mono text-xs bg-[#FF00FF] text-black border-2 border-black px-2 py-0.5 shadow-[2px_2px_0_#000000] font-black">
                MCP v2.0
              </span>
            </h1>
            <p className="mono text-xs font-bold uppercase text-black mt-0.5 tracking-wider">
              ARXIV LITERATURE // KAGGLE DATASETS // PANDAS CLEANING ENGINE
            </p>
          </div>
        </div>

        {/* Model Switcher */}
        <div className="flex items-center gap-2 border-4 border-black bg-white p-1.5 shadow-[4px_4px_0_#000000]">
          <span className="mono text-xs font-black uppercase text-black px-1.5">
            ENGINE:
          </span>
          {(["gemini", "groq", "ollama"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setProvider(m)}
              aria-label={`Select ${m} model provider`}
              className={`px-3 py-1 font-black text-xs uppercase border-2 border-black cursor-pointer ${
                provider === m
                  ? "bg-[#0000FF] text-white shadow-[2px_2px_0_#000000]"
                  : "bg-white text-black hover:bg-[#FFFF00]"
              }`}
            >
              {m === "gemini" ? "GEMINI 2.5" : m === "groq" ? "GROQ 70B" : "OLLAMA LOCAL"}
            </button>
          ))}
        </div>
      </header>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto my-4 space-y-5 pr-1">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
          >
            {/* User Message */}
            {msg.role === "user" ? (
              <div className="bg-[#0000FF] text-white border-4 border-black p-4 shadow-[6px_6px_0_#000000] max-w-2xl font-bold text-sm leading-relaxed">
                <div className="mono text-[10px] uppercase tracking-widest text-[#FFFF00] mb-1 font-black">
                  [USER QUERY]
                </div>
                {msg.content}
              </div>
            ) : (
              /* Assistant Message */
              <div className="w-full max-w-5xl bg-white border-4 border-black p-5 md:p-6 shadow-[8px_8px_0_#000000] text-black">
                <div className="mono text-[10px] uppercase tracking-widest text-black bg-[#FFFF00] border-2 border-black px-2 py-0.5 inline-block font-black mb-3 shadow-[2px_2px_0_#000000]">
                  [AMRA COGNITIVE CORE]
                </div>

                {/* Text Content */}
                {msg.content && (
                  <div className="text-sm font-bold text-black leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </div>
                )}

                {/* arXiv Papers Cards */}
                {msg.papers && msg.papers.length > 0 && (
                  <div className="mt-5 pt-4 border-t-4 border-black">
                    <h3 className="text-xs font-black uppercase text-black bg-[#FFFF00] border-2 border-black px-2.5 py-1 inline-flex items-center gap-1.5 shadow-[2px_2px_0_#000000] mb-3">
                      <Sparkles className="w-4 h-4" aria-hidden="true" />
                      VERIFIED ARXIV LITERATURE ({msg.papers.length})
                    </h3>
                    <div className="grid-brut">
                      {msg.papers.map((p: any) => (
                        <PaperCard key={p.id} paper={p} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Kaggle Dataset Cards */}
                {msg.datasets && msg.datasets.length > 0 && (
                  <div className="mt-5 pt-4 border-t-4 border-black">
                    <h3 className="text-xs font-black uppercase text-black bg-[#00FF00] border-2 border-black px-2.5 py-1 inline-flex items-center gap-1.5 shadow-[2px_2px_0_#000000] mb-3">
                      <Database className="w-4 h-4" aria-hidden="true" />
                      DISCOVERED DATASETS ({msg.datasets.length})
                    </h3>
                    <div className="grid-brut">
                      {msg.datasets.map((d: any) => (
                        <DatasetCard key={d.dataset_id} dataset={d} />
                      ))}
                    </div>
                  </div>
                )}

                {/* HITL Action Card */}
                {msg.approvalRequest && (
                  <ApprovalPrompt
                    data={msg.approvalRequest}
                    onApprove={(tok) => handleApprovePipeline(tok, msg.id)}
                    isLoading={isStreaming}
                  />
                )}

                {/* Data Preview Table */}
                {msg.pipelineResult && (
                  <DataPreviewTable data={msg.pipelineResult} />
                )}

                {/* Cost & Token Audit Badge */}
                {msg.costAudit && (
                  <div className="flex flex-wrap items-center gap-3 mt-4 pt-3 border-t-4 border-black text-xs font-mono font-black uppercase text-black">
                    <span className="bg-[#00FF00] text-black border-2 border-black px-2.5 py-1 shadow-[2px_2px_0_#000000] flex items-center gap-1">
                      <DollarSign className="w-3.5 h-3.5" aria-hidden="true" />
                      COST: $0.00 FREE TIER
                    </span>
                    <span className="bg-white text-black border-2 border-black px-2.5 py-1 shadow-[2px_2px_0_#000000]">
                      PROVIDER: {msg.costAudit.provider}
                    </span>
                    <span className="bg-[#FFFF00] text-black border-2 border-black px-2.5 py-1 shadow-[2px_2px_0_#000000]">
                      TOKENS: {msg.costAudit.prompt_tokens + msg.costAudit.completion_tokens}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {/* Live Thought Indicator */}
        {currentThought && (
          <div
            role="status"
            aria-live="polite"
            className="flex items-center gap-3 text-xs font-mono font-black uppercase text-black bg-[#FFFF00] border-4 border-black px-4 py-3 shadow-[6px_6px_0_#000000]"
          >
            <Cpu className="w-5 h-5 text-black shrink-0" aria-hidden="true" />
            <span>REASONING IN PROGRESS &gt;&gt;&gt; {currentThought}</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Brutalist Input Bar */}
      <form onSubmit={handleSubmit} className="flex gap-3 pt-3 border-t-4 border-black">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="ENTER RESEARCH HYPOTHESIS OR CLEANING INSTRUCTION..."
          disabled={isStreaming}
          aria-label="Research hypothesis prompt"
          className="flex-1 bg-white border-4 border-black px-4 py-3.5 text-sm font-bold text-black placeholder:text-black/60 placeholder:font-bold placeholder:uppercase focus:outline-none focus:bg-[#FFFF00] shadow-[4px_4px_0_#000000]"
        />
        <button
          type="submit"
          disabled={!input.trim() || isStreaming}
          aria-label="Send query"
          className="button button--blue px-6 py-3.5 text-sm font-black uppercase shadow-[4px_4px_0_#000000] flex items-center gap-2 cursor-pointer disabled:opacity-40"
        >
          <span>EXECUTE</span>
          <Send className="w-4 h-4" aria-hidden="true" />
        </button>
      </form>
    </div>
  );
};
