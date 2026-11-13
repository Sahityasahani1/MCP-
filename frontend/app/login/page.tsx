"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Brain,
  Lock,
  Mail,
  User,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  ArrowLeft,
  KeyRound,
} from "lucide-react";
import { getApiBaseUrl } from "../../lib/sse-client";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const apiBaseUrl = getApiBaseUrl();

  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Check for OAuth callback token in URL query parameter
  useEffect(() => {
    const token = searchParams.get("token");
    const error = searchParams.get("error");

    if (error) {
      setErrorMessage(`Authentication error: ${decodeURIComponent(error)}`);
    } else if (token) {
      localStorage.setItem("amra_auth_token", token);
      setSuccessMessage("Authentication successful! Redirecting to research workspace...");
      setTimeout(() => {
        router.push("/");
      }, 800);
    }
  }, [searchParams, router]);

  // Handle Local Email/Password Sign In or Sign Up
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsLoading(true);

    try {
      if (mode === "signup") {
        if (!fullName.trim()) {
          throw new Error("Please enter your full name.");
        }
        if (password.length < 8) {
          throw new Error("Password must be at least 8 characters long.");
        }

        const res = await fetch(`${apiBaseUrl}/api/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: email.trim().toLowerCase(),
            password,
            full_name: fullName.trim(),
          }),
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || "Registration failed. Please try again.");
        }

        localStorage.setItem("amra_auth_token", data.access_token);
        setSuccessMessage(`Account created for ${data.user.full_name}! Redirecting...`);
        setTimeout(() => router.push("/"), 800);
      } else {
        const res = await fetch(`${apiBaseUrl}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: email.trim().toLowerCase(),
            password,
          }),
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || "Invalid email or password.");
        }

        localStorage.setItem("amra_auth_token", data.access_token);
        setSuccessMessage(`Welcome back, ${data.user.full_name}! Redirecting...`);
        setTimeout(() => router.push("/"), 800);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  // Trigger Live OAuth 2.0 flow
  const handleLiveOAuth = (provider: "google" | "github" | "microsoft") => {
    setErrorMessage(null);
    const redirectUrl = `${apiBaseUrl}/api/auth/oauth/${provider}`;
    window.location.href = redirectUrl;
  };

  // Instant 1-Click Sandbox Social Sign-In (Works immediately without pre-configured cloud credentials)
  const handleDevMockLogin = async (provider: "google" | "github" | "microsoft") => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`${apiBaseUrl}/api/auth/oauth/dev-mock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to sign in with mock identity.");
      }

      localStorage.setItem("amra_auth_token", data.access_token);
      setSuccessMessage(`Signed in as ${data.user.full_name} (${provider.toUpperCase()})! Redirecting...`);
      setTimeout(() => router.push("/"), 800);
    } catch (err: any) {
      setErrorMessage(err.message || "Dev sign-in failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white text-black p-4 md:p-8 flex flex-col justify-between font-sans">
      {/* Top Header */}
      <header className="max-w-md w-full mx-auto flex items-center justify-between pb-6">
        <a
          href="/"
          className="inline-flex items-center gap-2 px-3 py-1.5 bg-white text-black border-4 border-black shadow-[4px_4px_0_#000000] font-mono text-xs font-black uppercase hover:bg-[#FFFF00] transition-transform active:translate-x-1 active:translate-y-1"
        >
          <ArrowLeft className="w-4 h-4" /> BACK TO WORKSPACE
        </a>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-[#00FF00] border-2 border-black animate-pulse" />
          <span className="font-mono text-xs font-black uppercase">DB CONNECTED</span>
        </div>
      </header>

      {/* Main Authentication Card */}
      <main className="max-w-md w-full mx-auto my-auto">
        <div className="border-8 border-black bg-white shadow-[12px_12px_0_#000000] p-6 md:p-8">
          {/* Brand Banner */}
          <div className="flex items-center gap-3 pb-6 border-b-4 border-black mb-6">
            <div className="p-3 bg-[#FFFF00] text-black border-4 border-black shadow-[4px_4px_0_#000000]">
              <Brain className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-black uppercase tracking-tight">AMRA</h1>
                <span className="font-mono text-[10px] bg-[#00FFFF] text-black border-2 border-black px-1.5 py-0.5 font-black">
                  AUTH v2.0
                </span>
              </div>
              <p className="font-mono text-xs text-slate-700 font-bold uppercase mt-0.5">
                Multi-Tenant Research Access
              </p>
            </div>
          </div>

          {/* Mode Tabs (Sign In vs Sign Up) */}
          <div className="grid grid-cols-2 gap-2 mb-6 border-4 border-black p-1 bg-black">
            <button
              type="button"
              onClick={() => {
                setMode("signin");
                setErrorMessage(null);
              }}
              className={`py-2 text-xs font-black uppercase font-mono tracking-wider transition-all cursor-pointer ${
                mode === "signin"
                  ? "bg-[#FFFF00] text-black shadow-[2px_2px_0_#FFFFFF]"
                  : "bg-transparent text-white hover:text-[#FFFF00]"
              }`}
            >
              SIGN IN
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("signup");
                setErrorMessage(null);
              }}
              className={`py-2 text-xs font-black uppercase font-mono tracking-wider transition-all cursor-pointer ${
                mode === "signup"
                  ? "bg-[#00FF00] text-black shadow-[2px_2px_0_#FFFFFF]"
                  : "bg-transparent text-white hover:text-[#00FF00]"
              }`}
            >
              CREATE ACCOUNT
            </button>
          </div>

          {/* Error Message */}
          {errorMessage && (
            <div
              role="alert"
              className="mb-6 p-3 bg-[#FF0000] text-white border-4 border-black shadow-[4px_4px_0_#000000] flex items-start gap-2.5 font-mono text-xs font-black"
            >
              <AlertTriangle className="w-5 h-5 shrink-0 text-[#FFFF00]" />
              <div>{errorMessage}</div>
            </div>
          )}

          {/* Success Message */}
          {successMessage && (
            <div
              role="status"
              className="mb-6 p-3 bg-[#00FF00] text-black border-4 border-black shadow-[4px_4px_0_#000000] flex items-center gap-2.5 font-mono text-xs font-black"
            >
              <CheckCircle2 className="w-5 h-5 shrink-0" />
              <div>{successMessage}</div>
            </div>
          )}

          {/* Email / Password Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "signup" && (
              <div>
                <label className="block font-mono text-xs font-black uppercase mb-1.5 flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5" /> Full Name
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Dr. Ada Lovelace"
                  className="w-full p-2.5 border-4 border-black bg-white text-black font-mono text-xs font-bold outline-none focus:bg-[#FFFF00]/10 shadow-[4px_4px_0_#000000]"
                />
              </div>
            )}

            <div>
              <label className="block font-mono text-xs font-black uppercase mb-1.5 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5" /> Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="researcher@university.edu"
                className="w-full p-2.5 border-4 border-black bg-white text-black font-mono text-xs font-bold outline-none focus:bg-[#FFFF00]/10 shadow-[4px_4px_0_#000000]"
              />
            </div>

            <div>
              <label className="block font-mono text-xs font-black uppercase mb-1.5 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5" /> Password {mode === "signup" && "(min 8 chars)"}
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full p-2.5 border-4 border-black bg-white text-black font-mono text-xs font-bold outline-none focus:bg-[#FFFF00]/10 shadow-[4px_4px_0_#000000]"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className={`w-full mt-2 py-3 px-4 border-4 border-black font-mono text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 shadow-[6px_6px_0_#000000] cursor-pointer transition-transform active:translate-x-1 active:translate-y-1 ${
                mode === "signup"
                  ? "bg-[#00FF00] hover:bg-black hover:text-[#00FF00]"
                  : "bg-[#FFFF00] hover:bg-black hover:text-[#FFFF00]"
              }`}
            >
              {isLoading ? (
                "AUTHENTICATING..."
              ) : mode === "signup" ? (
                <>
                  REGISTER ACCOUNT <ArrowRight className="w-4 h-4" />
                </>
              ) : (
                <>
                  SIGN IN TO WORKSPACE <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-8 text-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t-4 border-black"></div>
            </div>
            <div className="relative inline-block bg-white px-3 font-mono text-xs font-black uppercase tracking-wider text-black border-2 border-black">
              OR CONNECT SOCIAL ID
            </div>
          </div>

          {/* Social OAuth Buttons */}
          <div className="space-y-2.5">
            {/* Google / Gmail */}
            <button
              type="button"
              onClick={() => handleLiveOAuth("google")}
              disabled={isLoading}
              className="w-full p-2.5 bg-white text-black border-4 border-black font-mono text-xs font-black uppercase flex items-center justify-center gap-3 shadow-[4px_4px_0_#000000] hover:bg-[#FFFF00] cursor-pointer transition-transform active:translate-x-1 active:translate-y-1"
            >
              {/* Google G SVG */}
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              CONTINUE WITH GOOGLE (GMAIL)
            </button>

            {/* GitHub */}
            <button
              type="button"
              onClick={() => handleLiveOAuth("github")}
              disabled={isLoading}
              className="w-full p-2.5 bg-white text-black border-4 border-black font-mono text-xs font-black uppercase flex items-center justify-center gap-3 shadow-[4px_4px_0_#000000] hover:bg-[#00FFFF] cursor-pointer transition-transform active:translate-x-1 active:translate-y-1"
            >
              {/* GitHub Octocat SVG */}
              <svg className="w-4 h-4 fill-black" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
              CONTINUE WITH GITHUB
            </button>

            {/* Microsoft / Outlook */}
            <button
              type="button"
              onClick={() => handleLiveOAuth("microsoft")}
              disabled={isLoading}
              className="w-full p-2.5 bg-white text-black border-4 border-black font-mono text-xs font-black uppercase flex items-center justify-center gap-3 shadow-[4px_4px_0_#000000] hover:bg-[#FF00FF] cursor-pointer transition-transform active:translate-x-1 active:translate-y-1"
            >
              {/* Microsoft 4-square SVG */}
              <svg className="w-4 h-4" viewBox="0 0 21 21">
                <rect x="1" y="1" width="9" height="9" fill="#f25022" />
                <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
                <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
                <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
              </svg>
              CONTINUE WITH OUTLOOK (MICROSOFT)
            </button>
          </div>

          {/* Developer Sandbox 1-Click Test Badges */}
          <div className="mt-6 pt-4 border-t-2 border-dashed border-black">
            <div className="flex items-center gap-1.5 mb-2 font-mono text-[10px] font-black uppercase text-slate-700">
              <Sparkles className="w-3.5 h-3.5 text-[#0000FF]" />
              <span>1-Click Sandbox Social Identities:</span>
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              <button
                type="button"
                onClick={() => handleDevMockLogin("google")}
                className="py-1 px-1.5 bg-white border-2 border-black font-mono text-[9px] font-black uppercase hover:bg-[#FFFF00] cursor-pointer truncate shadow-[2px_2px_0_#000000]"
                title="Instant login as Google Researcher"
              >
                + Google
              </button>
              <button
                type="button"
                onClick={() => handleDevMockLogin("github")}
                className="py-1 px-1.5 bg-white border-2 border-black font-mono text-[9px] font-black uppercase hover:bg-[#00FFFF] cursor-pointer truncate shadow-[2px_2px_0_#000000]"
                title="Instant login as GitHub Engineer"
              >
                + GitHub
              </button>
              <button
                type="button"
                onClick={() => handleDevMockLogin("microsoft")}
                className="py-1 px-1.5 bg-white border-2 border-black font-mono text-[9px] font-black uppercase hover:bg-[#FF00FF] cursor-pointer truncate shadow-[2px_2px_0_#000000]"
                title="Instant login as Outlook Scientist"
              >
                + Outlook
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Footer Security Badges */}
      <footer className="max-w-md w-full mx-auto pt-6 text-center">
        <div className="flex items-center justify-center gap-3 font-mono text-[10px] font-black uppercase text-slate-600">
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-[#00FF00]" /> NIST PBKDF2
          </span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <KeyRound className="w-3.5 h-3.5 text-[#0000FF]" /> JWT AUTH
          </span>
          <span>•</span>
          <span>SQLITE WAL</span>
        </div>
      </footer>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-white text-black p-8 font-mono text-xs font-black uppercase flex items-center justify-center">
          Loading Authentication Portal...
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
