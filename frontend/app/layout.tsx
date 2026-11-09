import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AMRA // AUTONOMOUS ML RESEARCH AGENT [MCP v2.0]",
  description: "Brutalist Model Context Protocol (MCP) AI Workspace for Literature Discovery & Tabular Cleaning",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-white text-black antialiased selection:bg-[#FFFF00] selection:text-black">
        {children}
      </body>
    </html>
  );
}
