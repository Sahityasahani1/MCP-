"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Sparkles,
  Brain,
  Cpu,
  Database,
  ShieldCheck,
  DollarSign,
  RefreshCw,
  Square,
  AlertTriangle,
  X,
  ArrowRight,
  Flame,
  History,
  FileDown,
  UploadCloud,
  User,
  LogOut,
  LogIn,
  Cloud,
} from "lucide-react";
import { consumeSSEStream, getApiBaseUrl, getAuthHeaders } from "../lib/sse-client";
import { PaperCard } from "./PaperCard";
import { DatasetCard } from "./DatasetCard";
import { ApprovalPrompt } from "./ApprovalPrompt";
import { DataPreviewTable } from "./DataPreviewTable";
import { SessionSidebar } from "./SessionSidebar";
import { DossierExport } from "./DossierExport";
import { FileUploadModal } from "./FileUploadModal";

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

const STARTER_PRESETS = [
  {
    label: "🔍 SOTA GNNs for Fraud",
    prompt:
      "Find state-of-the-art papers on Graph Neural Networks for financial fraud detection and locate a verified benchmark dataset.",
    tag: "LITERATURE + DATASET",
    tagColor: "bg-[#FFFF00]",
  },
  {
    label: "📊 Source Churn & LightGBM",
    prompt:
      "Search for a telecom customer churn dataset and run the automated LightGBM baseline data cleaning pipeline.",
    tag: "DATA CLEANING + ML",
    tagColor: "bg-[#00FF00]",
  },
  {
    label: "⚡ Vision Transformers",
    prompt:
      "Survey recent high-citation papers on Vision Transformers and Multi-Modal Foundation Models with verified OA PDFs.",
    tag: "ARXIV + OPENALEX",
    tagColor: "bg-[#00FFFF]",
  },
  {
    label: "🧹 Clean Fraud & Export Parquet",
    prompt:
      "Download the credit card fraud dataset, perform IQR outlier winsorization, zero-leakage 80/20 train/test split, and export full Parquet partitions.",
    tag: "PIPELINE ENGINE",
    tagColor: "bg-[#FF00FF]",
  },
];

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Welcome to AMRA. Search peer-reviewed literature (arXiv & OpenAlex) and datasets (Kaggle & Hugging Face), or upload a CSV to clean and run baseline AutoML modeling.",
    },
  ]);
  const [input, setInput] = useState("");
  const [provider, setProvider] = useState<"gemini" | "groq" | "ollama">("gemini");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentThought, setCurrentThought] = useState<string | null>(null);
  const [activeError, setActiveError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const [sessionId, setSessionId] = useState<string>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("amra_active_session");
      if (stored) return stored;
    }
    return `sess_${Math.random().toString(36).substring(2, 10)}`;
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const apiBaseUrl = getApiBaseUrl();
  const [currentUser, setCurrentUser] = useState<any | null>(null);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/api/auth/me`, {
          headers: getAuthHeaders(),
        });
        if (res.ok) {
          const data = await res.json();
          // If developer default or real user, set
          setCurrentUser(data.user);
        } else {
          setCurrentUser(null);
        }
      } catch {
        setCurrentUser(null);
      }
    };
    fetchCurrentUser();
  }, [apiBaseUrl]);

  const handleSignOut = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("amra_auth_token");
    }
    setCurrentUser(null);
    window.location.reload();
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("amra_active_session", sessionId);
    }
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "auto" });
  }, [messages, currentThought]);

  // Dynamic Browser Tab Title Indicator
  useEffect(() => {
    if (typeof document === "undefined") return;
    if (isStreaming) {
      document.title = "(⚡ Reasoning...) AMRA // ML Agent";
    } else if (messages.length > 1) {
      document.title = "(✓ Ready) AMRA // ML Agent";
      const timer = setTimeout(() => {
        document.title = "AMRA // Autonomous ML Research Agent";
      }, 5000);
      return () => clearTimeout(timer);
    } else {
      document.title = "AMRA // Autonomous ML Research Agent";
    }
  }, [isStreaming, messages.length]);

  // Global Developer Hotkeys (Ctrl+K to focus input, Ctrl+U to upload, Esc to close/stop)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "u") {
        e.preventDefault();
        setIsUploadModalOpen((prev) => !prev);
      } else if (e.key === "Escape") {
        if (isUploadModalOpen) {
          setIsUploadModalOpen(false);
        } else if (sidebarOpen) {
          setSidebarOpen(false);
        } else if (isStreaming && abortControllerRef.current) {
          handleStopStreaming();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isUploadModalOpen, sidebarOpen, isStreaming]);

  const loadSession = async (targetSessionId: string) => {
    if (isStreaming) return;
    setActiveError(null);
    setSessionId(targetSessionId);
    try {
      const res = await fetch(`${apiBaseUrl}/api/chat/history/${targetSessionId}`, {
        cache: "no-store",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
          const loaded: Message[] = data.messages.map((m: any, idx: number) => ({
            id: `msg_${targetSessionId}_${idx}`,
            role: m.role,
            content: m.content,
            papers: m.metadata?.papers || [],
            datasets: m.metadata?.datasets || [],
            pipelineResult: m.metadata?.pipelineResult || null,
            costAudit: m.metadata?.costAudit || null,
          }));
          setMessages(loaded);
          setSidebarOpen(false);
          return;
        }
      }
    } catch (e) {
      console.warn("Failed to load session:", e);
    }
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: "Loaded research thread. Enter a prompt or select a suggested topic to continue.",
      },
    ]);
    setSidebarOpen(false);
  };

  const handleNewSession = () => {
    if (isStreaming) return;
    const newId = `sess_${Math.random().toString(36).substring(2, 10)}`;
    setSessionId(newId);
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: "New research thread initialized. Enter a topic or choose a prompt below.",
      },
    ]);
    setActiveError(null);
    setCurrentThought(null);
    setSidebarOpen(false);
  };

  const executeQuery = async (queryText: string) => {
    if (!queryText.trim() || isStreaming) return;

    setActiveError(null);
    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `asst_${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: queryText },
      { id: assistantMsgId, role: "assistant", thoughts: [], papers: [], datasets: [] },
    ]);

    setIsStreaming(true);
    setCurrentThought("Initializing reasoning loop...");

    const controller = new AbortController();
    abortControllerRef.current = controller;

    await consumeSSEStream(
      `${apiBaseUrl}/api/chat/stream`,
      { message: queryText, session_id: sessionId, provider },
      {
        onThought: (thought) => {
          setCurrentThought(thought);
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
            prev.map((m) =>
              m.id === assistantMsgId ? { ...m, approvalRequest: data } : m
            )
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
          abortControllerRef.current = null;
        },
        onError: (err) => {
          setIsStreaming(false);
          setCurrentThought(null);
          abortControllerRef.current = null;
          setActiveError(err);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? { ...m, content: `CRITICAL EXECUTION ERROR: ${err}` }
                : m
            )
          );
        },
      },
      controller.signal
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || isStreaming) return;
    setInput("");
    await executeQuery(query);
  };

  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setCurrentThought(null);
    setMessages((prev) => [
      ...prev,
      {
        id: `stop_${Date.now()}`,
        role: "system",
        content: "Stream stopped by user.",
      },
    ]);
  };

  const handleUploadSuccess = (datasetId: string, filename: string, previewInfo?: any) => {
    const promptText = `Clean and profile uploaded tabular dataset ${datasetId} (${filename}) with LightGBM baseline modeling`;
    setInput(promptText);
    executeQuery(promptText);
  };

  const handleCleanDataset = (datasetId: string) => {
    const promptText = `Clean and profile dataset ${datasetId} with LightGBM baseline modeling`;
    setInput(promptText);
    executeQuery(promptText);
  };

  const handleApprovePipeline = async (token: string, messageId: string, customRecipe?: any) => {
    setActiveError(null);
    setIsStreaming(true);
    setCurrentThought("EXECUTING HITL DATA CLEANING PIPELINE...");

    const controller = new AbortController();
    abortControllerRef.current = controller;

    await consumeSSEStream(
      `${apiBaseUrl}/api/chat/approve`,
      { approval_token: token, session_id: sessionId, custom_recipe: customRecipe },
      {
        onThought: (t) => setCurrentThought(t),
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
          abortControllerRef.current = null;
        },
        onError: (err) => {
          setIsStreaming(false);
          setCurrentThought(null);
          abortControllerRef.current = null;
          setActiveError(err);
        },
      },
      controller.signal
    );
  };

  return (
    <div className="flex flex-col h-screen max-w-6xl mx-auto p-4 md:p-6 bg-white text-black font-sans relative">
      {/* Session History Sidebar Drawer */}
      <SessionSidebar
        currentSessionId={sessionId}
        onSelectSession={loadSession}
        onNewSession={handleNewSession}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen((prev) => !prev)}
      />

      {/* Brutalist Top Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b-4 border-black gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen((prev) => !prev)}
            className="p-2.5 bg-white text-black border-4 border-black shadow-[4px_4px_0_#000000] hover:bg-[#FFFF00] flex items-center gap-1.5 font-mono text-xs font-black uppercase cursor-pointer"
            aria-label="Toggle research threads sidebar"
            title="Open Research Threads"
          >
            <History className="w-5 h-5" aria-hidden="true" />
            <span className="hidden sm:inline">THREADS</span>
          </button>

          <button
            onClick={() => setIsUploadModalOpen(true)}
            className="p-2.5 bg-[#00FF00] text-black border-4 border-black shadow-[4px_4px_0_#000000] hover:bg-black hover:text-[#00FF00] flex items-center gap-1.5 font-mono text-xs font-black uppercase cursor-pointer"
            aria-label="Upload custom CSV dataset"
            title="Upload Custom CSV Dataset (Ctrl+U)"
          >
            <UploadCloud className="w-5 h-5" aria-hidden="true" />
            <span className="hidden sm:inline">UPLOAD CSV</span>
            <span className="hidden lg:inline text-[9px] bg-black text-[#00FF00] px-1 font-mono">^U</span>
          </button>

          <a
            href="/cloudflare"
            className="p-2.5 bg-white text-black border-4 border-black shadow-[4px_4px_0_#000000] hover:bg-[#FF8000] hover:text-black flex items-center gap-1.5 font-mono text-xs font-black uppercase cursor-pointer"
            aria-label="Cloudflare Pages & Edge Caching"
            title="Cloudflare Pages & Edge Caching Dashboard"
          >
            <Cloud className="w-5 h-5" aria-hidden="true" />
            <span className="hidden xl:inline">EDGE CACHE</span>
          </a>

          <div className="p-2.5 bg-[#FFFF00] text-black border-4 border-black shadow-[4px_4px_0_#000000]">
            <Brain className="w-7 h-7" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-black uppercase tracking-tight text-black flex items-center gap-2">
              AMRA
              <span className="font-mono text-xs bg-[#FF00FF] text-black border-2 border-black px-2 py-0.5 shadow-[2px_2px_0_#000000] font-black">
                RESEARCH AGENT
              </span>
            </h1>
          </div>
        </div>

        {/* Model Switcher & User Profile */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5 border-4 border-black bg-white p-1.5 shadow-[4px_4px_0_#000000]">
            <span className="mono text-xs font-black uppercase text-black px-1">
              ENGINE:
            </span>
            {(["gemini", "groq", "ollama"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setProvider(m)}
                aria-label={`Select ${m} model provider`}
                className={`px-2.5 py-1 font-black text-xs uppercase border-2 border-black cursor-pointer ${
                  provider === m
                    ? "bg-[#0000FF] text-white shadow-[2px_2px_0_#000000]"
                    : "bg-white text-black hover:bg-[#FFFF00]"
                }`}
              >
                {m === "gemini" ? "GEMINI 3.8" : m === "groq" ? "GROQ 120B" : "OLLAMA"}
              </button>
            ))}
          </div>

          {/* User Profile Pill or Sign In Button */}
          {currentUser && currentUser.id !== "usr_default_dev" ? (
            <div className="flex items-center gap-2 border-4 border-black bg-white p-1.5 shadow-[4px_4px_0_#000000]">
              <div className="flex items-center gap-1.5 px-1">
                {currentUser.avatar_url ? (
                  <img
                    src={currentUser.avatar_url}
                    alt={currentUser.full_name}
                    className="w-6 h-6 border-2 border-black bg-[#FFFF00] object-cover"
                  />
                ) : (
                  <div className="w-6 h-6 border-2 border-black bg-[#00FFFF] flex items-center justify-center font-mono font-black text-[10px]">
                    {currentUser.full_name?.charAt(0) || "U"}
                  </div>
                )}
                <div className="flex flex-col text-left">
                  <span className="font-mono text-[11px] font-black uppercase text-black max-w-[120px] truncate leading-tight">
                    {currentUser.full_name}
                  </span>
                  <span className="font-mono text-[9px] font-bold text-slate-600 uppercase leading-none">
                    {currentUser.provider}
                  </span>
                </div>
              </div>
              <button
                onClick={handleSignOut}
                className="p-1.5 bg-[#FF0000] text-white border-2 border-black hover:bg-black hover:text-[#FF0000] cursor-pointer"
                title="Sign Out"
                aria-label="Sign Out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <a
              href="/login"
              className="px-3 py-2 bg-[#00FF00] text-black border-4 border-black shadow-[4px_4px_0_#000000] hover:bg-black hover:text-[#00FF00] font-mono text-xs font-black uppercase flex items-center gap-1.5 cursor-pointer transition-transform active:translate-x-1 active:translate-y-1"
            >
              <LogIn className="w-4 h-4" />
              <span>SIGN IN</span>
            </a>
          )}
        </div>
      </header>

      {/* Dismissible Error Alert Banner */}
      {activeError && (
        <div
          role="alert"
          className="mt-4 p-3 bg-[#FF0000] text-black border-4 border-black shadow-[6px_6px_0_#000000] flex items-center justify-between gap-3 font-mono text-xs font-black uppercase"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-[#FFFF00] shrink-0" aria-hidden="true" />
            <span>ERROR: {activeError}</span>
          </div>
          <button
            onClick={() => setActiveError(null)}
            className="p-1 bg-white text-black border-2 border-black hover:bg-black hover:text-white cursor-pointer"
            aria-label="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto my-4 space-y-5 pr-1">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.role === "user"
                ? "items-end"
                : msg.role === "system"
                ? "items-center"
                : "items-start"
            }`}
          >
            {/* System Notification */}
            {msg.role === "system" ? (
              <div className="bg-[#FFFF00] text-black border-3 border-black px-4 py-2 font-mono text-xs font-black uppercase shadow-[4px_4px_0_#000000] inline-flex items-center gap-2 my-2">
                <AlertTriangle className="w-4 h-4" aria-hidden="true" />
                <span>{msg.content}</span>
              </div>
            ) : msg.role === "user" ? (
              /* User Message */
              <div className="bg-[#0000FF] text-white border-4 border-black p-4 shadow-[6px_6px_0_#000000] max-w-2xl font-bold text-sm leading-relaxed">
                <div className="mono text-[10px] uppercase tracking-widest text-[#FFFF00] mb-1 font-black">
                  YOU
                </div>
                {msg.content}
              </div>
            ) : (
              /* Assistant Message */
              <div className="w-full max-w-5xl bg-white border-4 border-black p-5 md:p-6 shadow-[8px_8px_0_#000000] text-black">
                <div className="mb-3">
                  <span className="mono text-[10px] uppercase tracking-widest text-black bg-[#FFFF00] border-2 border-black px-2 py-0.5 inline-block font-black shadow-[2px_2px_0_#000000]">
                    AMRA
                  </span>
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
                      RESEARCH PAPERS ({msg.papers.length})
                    </h3>
                    <div className="grid-brut">
                      {msg.papers.map((p: any) => (
                        <PaperCard key={p.id} paper={p} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Kaggle & HF Dataset Cards */}
                {msg.datasets && msg.datasets.length > 0 && (
                  <div className="mt-5 pt-4 border-t-4 border-black">
                    <h3 className="text-xs font-black uppercase text-black bg-[#00FF00] border-2 border-black px-2.5 py-1 inline-flex items-center gap-1.5 shadow-[2px_2px_0_#000000] mb-3">
                      <Database className="w-4 h-4" aria-hidden="true" />
                      DATASETS ({msg.datasets.length})
                    </h3>
                    <div className="grid-brut">
                      {msg.datasets.map((d: any) => (
                        <DatasetCard
                          key={d.dataset_id}
                          dataset={d}
                          onClean={handleCleanDataset}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* HITL Action Card */}
                {msg.approvalRequest && (
                  <ApprovalPrompt
                    data={msg.approvalRequest}
                    onApprove={(tok, customRecipe) => handleApprovePipeline(tok, msg.id, customRecipe)}
                    isLoading={isStreaming}
                  />
                )}

                {/* Data Preview Table */}
                {msg.pipelineResult && (
                  <DataPreviewTable data={msg.pipelineResult} />
                )}

                {/* Research Dossier Export Bar (Markdown & BibTeX) */}
                <DossierExport
                  sessionId={sessionId}
                  papers={msg.papers}
                  datasets={msg.datasets}
                  pipelineResult={msg.pipelineResult}
                />

                {/* Telemetry Audit */}
                {msg.costAudit && (
                  <div className="flex flex-wrap items-center gap-2 mt-3 pt-2.5 border-t-2 border-black text-xs font-mono font-bold text-slate-700">
                    <span className="bg-[#00FF00] text-black px-2 py-0.5 border border-black font-black flex items-center gap-1 shadow-[1px_1px_0_#000000]">
                      <DollarSign className="w-3 h-3" aria-hidden="true" />
                      $0.00
                    </span>
                    <span>{msg.costAudit.provider} / {msg.costAudit.model}</span>
                    <span>•</span>
                    <span>{msg.costAudit.prompt_tokens + msg.costAudit.completion_tokens} tokens</span>
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
            <Cpu className="w-5 h-5 text-black shrink-0 animate-pulse" aria-hidden="true" />
            <span>{currentThought}</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Starter Suggestion Chips (Available When Idle) */}
      {!isStreaming && messages.length <= 2 && (
        <div className="mb-3">
          <div className="text-[10px] font-mono font-black uppercase text-black mb-1.5 flex items-center gap-1">
            <Flame className="w-3.5 h-3.5 text-[#FF0000]" aria-hidden="true" />
            <span>SUGGESTED PROMPTS:</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {STARTER_PRESETS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => executeQuery(preset.prompt)}
                className="text-left bg-white text-black border-3 border-black p-2.5 shadow-[3px_3px_0_#000000] hover:bg-[#FFFF00] hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[1px_1px_0_#000000] transition-none cursor-pointer flex flex-col justify-between group"
              >
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="font-black text-xs uppercase group-hover:underline">
                    {preset.label}
                  </span>
                  <span
                    className={`font-mono text-[9px] font-black px-1.5 py-0.2 border border-black ${preset.tagColor}`}
                  >
                    {preset.tag}
                  </span>
                </div>
                <p className="text-[11px] font-bold text-black/80 line-clamp-2">
                  {preset.prompt}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Brutalist Input Bar with Stream Cancellation */}
      <form onSubmit={handleSubmit} className="flex gap-3 pt-3 border-t-4 border-black">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            isStreaming
              ? "Reasoning in progress... click Stop to abort"
              : "Enter research topic or cleaning prompt... (Ctrl+K)"
          }
          disabled={isStreaming}
          aria-label="Research hypothesis prompt"
          className="flex-1 bg-white border-4 border-black px-4 py-3.5 text-sm font-bold text-black placeholder:text-black/60 placeholder:font-bold placeholder:uppercase focus:outline-none focus:bg-[#FFFF00] shadow-[4px_4px_0_#000000] disabled:bg-neutral-100"
        />

        {isStreaming ? (
          <button
            type="button"
            onClick={handleStopStreaming}
            aria-label="Stop generation"
            className="button bg-[#FF0000] text-black hover:bg-black hover:text-white px-6 py-3.5 text-sm font-black uppercase shadow-[4px_4px_0_#000000] flex items-center gap-2 cursor-pointer border-4 border-black"
          >
            <Square className="w-4 h-4 fill-current" aria-hidden="true" />
            <span>STOP</span>
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            aria-label="Send query"
            className="button button--blue px-6 py-3.5 text-sm font-black uppercase shadow-[4px_4px_0_#000000] flex items-center gap-2 cursor-pointer disabled:opacity-40"
          >
            <span>EXECUTE</span>
            <Send className="w-4 h-4" aria-hidden="true" />
          </button>
        )}
      </form>

      {/* Custom Tabular Dataset Upload Modal */}
      <FileUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  );
};
