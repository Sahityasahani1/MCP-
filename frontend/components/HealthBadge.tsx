"use client";

import React, { useState, useEffect } from "react";
import { Activity, Wifi, WifiOff } from "lucide-react";
import { getApiBaseUrl } from "../lib/sse-client";

interface HealthData {
  status: string;
  service: string;
  version: string;
  configured_provider: string;
  has_gemini_key: boolean;
  has_groq_key: boolean;
}

export const HealthBadge: React.FC<{ activeProvider: string }> = ({ activeProvider }) => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(true);

  const checkHealth = async () => {
    const apiBaseUrl = getApiBaseUrl();
    const start = performance.now();
    try {
      const res = await fetch(`${apiBaseUrl}/api/health`, {
        cache: "no-store",
      });
      const end = performance.now();
      if (res.ok) {
        const data: HealthData = await res.json();
        setHealth(data);
        setLatency(Math.round(end - start));
        setIsOnline(true);
      } else {
        setIsOnline(false);
      }
    } catch {
      setIsOnline(false);
      setLatency(null);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, [activeProvider]);

  return (
    <div className="flex items-center gap-2 font-mono text-[11px] font-black uppercase text-black">
      {isOnline ? (
        <div className="bg-[#00FF00] text-black border-2 border-black px-2.5 py-1 shadow-[2px_2px_0_#000000] inline-flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-black animate-pulse" aria-hidden="true" />
          <span>FASTAPI: {latency !== null ? `${latency}MS` : "ONLINE"}</span>
        </div>
      ) : (
        <div className="bg-[#FF0000] text-white border-2 border-black px-2.5 py-1 shadow-[2px_2px_0_#000000] inline-flex items-center gap-1.5">
          <WifiOff className="w-3.5 h-3.5 text-white" aria-hidden="true" />
          <span>FASTAPI: OFFLINE</span>
        </div>
      )}

      <div className="bg-white text-black border-2 border-black px-2.5 py-1 shadow-[2px_2px_0_#000000] hidden sm:inline-flex items-center gap-1">
        <Activity className="w-3.5 h-3.5 text-blue-700" aria-hidden="true" />
        <span>ACTIVE: {activeProvider.toUpperCase()}</span>
      </div>
    </div>
  );
};
