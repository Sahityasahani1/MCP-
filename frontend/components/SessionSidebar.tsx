"use client";

import React, { useState, useEffect } from "react";
import { MessageSquare, Plus, Clock, ChevronLeft, ChevronRight, RefreshCw, Trash2 } from "lucide-react";
import { getApiBaseUrl, getAuthHeaders } from "../lib/sse-client";

export interface SessionMeta {
  session_id: string;
  message_count: number;
  last_updated: number;
  title: string;
}

interface SessionSidebarProps {
  currentSessionId: string;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

export const SessionSidebar: React.FC<SessionSidebarProps> = ({
  currentSessionId,
  onSelectSession,
  onNewSession,
  isOpen,
  onToggle,
}) => {
  const [sessions, setSessions] = useState<SessionMeta[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchSessions = async () => {
    setLoading(true);
    const apiBaseUrl = getApiBaseUrl();
    try {
      const res = await fetch(`${apiBaseUrl}/api/chat/sessions?limit=25`, {
        cache: "no-store",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch (e) {
      console.warn("Failed to fetch sessions:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchSessions();
    }
  }, [isOpen, currentSessionId]);

  const formatDate = (timestamp: number) => {
    try {
      const d = new Date(timestamp * 1000);
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "Recent";
    }
  };

  return (
    <>
      {/* Sliding Drawer Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-72 md:w-80 bg-white border-r-4 border-black p-4 shadow-[8px_0_0_#000000] flex flex-col transition-transform duration-200 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        aria-label="Research threads history"
      >
        {/* Top Action Header */}
        <div className="flex items-center justify-between pb-3 border-b-4 border-black">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-black" aria-hidden="true" />
            <h3 className="font-black text-sm uppercase tracking-tight text-black">
              RESEARCH THREADS
            </h3>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={fetchSessions}
              disabled={loading}
              className="p-1 border-2 border-black bg-white hover:bg-[#FFFF00] cursor-pointer"
              title="Refresh sessions"
              aria-label="Refresh sessions"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={onToggle}
              className="p-1 border-2 border-black bg-white hover:bg-[#FF0000] hover:text-white cursor-pointer"
              aria-label="Close sidebar"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* New Session Button */}
        <button
          onClick={onNewSession}
          className="my-3 button button--blue w-full py-2.5 text-xs font-black uppercase shadow-[3px_3px_0_#000000] flex items-center justify-center gap-2 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>NEW THREAD</span>
        </button>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {sessions.length === 0 ? (
            <div className="p-4 bg-neutral-100 border-2 border-black text-xs font-mono text-center text-neutral-600 uppercase">
              No previous threads
            </div>
          ) : (
            sessions.map((s) => {
              const isActive = s.session_id === currentSessionId;
              return (
                <div
                  key={s.session_id}
                  onClick={() => onSelectSession(s.session_id)}
                  className={`p-2.5 border-3 border-black text-xs cursor-pointer transition-none ${
                    isActive
                      ? "bg-[#FFFF00] shadow-[3px_3px_0_#000000] font-black"
                      : "bg-white hover:bg-neutral-100 shadow-[2px_2px_0_#000000]"
                  }`}
                >
                  <div className="font-bold text-black line-clamp-2 leading-snug">
                    {s.title}
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-mono font-bold text-neutral-600 mt-2 pt-1 border-t border-black/30">
                    <span className="flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5" />
                      <span>{formatDate(s.last_updated)}</span>
                    </span>
                    <span className="bg-black text-white px-1.5 py-0.2 text-[9px] font-black">
                      {s.message_count} MSGS
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Info */}
        <div className="pt-3 border-t-3 border-black text-[10px] font-mono font-black uppercase text-neutral-600 text-center">
          SQLITE WAL SESSION STORE // AMRA v2.0
        </div>
      </aside>

      {/* Backdrop overlay for mobile */}
      {isOpen && (
        <div
          onClick={onToggle}
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          aria-hidden="true"
        />
      )}
    </>
  );
};
