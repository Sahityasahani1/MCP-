"use client";

import React from "react";
import { BookOpen, FileText, ExternalLink, Calendar, Users, Award, BookmarkCheck } from "lucide-react";

interface PaperProps {
  paper: {
    id: string;
    title: string;
    authors: string[];
    published: string;
    summary: string;
    pdf_url: string;
    source?: string;
    citation_count?: number | null;
    doi?: string;
  };
}

export const PaperCard: React.FC<PaperProps> = ({ paper }) => {
  const sourceName = (paper.source || "arXiv").toUpperCase();
  const isArxiv = sourceName === "ARXIV";

  return (
    <div className="bg-[#FFFF00] text-black border-4 border-black p-4 my-2 shadow-[6px_6px_0_#000000]">
      {/* Top Meta Bar */}
      <div className="flex items-start justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="bg-white text-black border-2 border-black font-mono font-black text-xs px-2.5 py-0.5 inline-flex items-center gap-1.5 shadow-[2px_2px_0_#000000]">
            <BookOpen className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{sourceName}: {paper.id}</span>
          </div>

          {paper.citation_count !== undefined && paper.citation_count !== null && (
            <div className="bg-[#00FF00] text-black border-2 border-black font-mono font-black text-xs px-2.5 py-0.5 inline-flex items-center gap-1.5 shadow-[2px_2px_0_#000000]">
              <Award className="w-3.5 h-3.5" aria-hidden="true" />
              <span>{paper.citation_count.toLocaleString()} CITATIONS</span>
            </div>
          )}

          {!isArxiv && (
            <div className="bg-[#00FFFF] text-black border-2 border-black font-mono font-black text-[10px] px-2 py-0.5 uppercase shadow-[2px_2px_0_#000000] inline-flex items-center gap-1">
              <BookmarkCheck className="w-3 h-3" aria-hidden="true" />
              <span>PEER REVIEWED</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {paper.doi && (
            <a
              href={paper.doi.startsWith("http") ? paper.doi : `https://doi.org/${paper.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Open DOI link for ${paper.title}`}
              className="bg-white text-black text-xs font-black uppercase px-2.5 py-1 border-2 border-black shadow-[2px_2px_0_#000000] hover:bg-[#FF00FF] hover:text-white inline-flex items-center gap-1 transition-none"
            >
              <span>DOI</span>
              <ExternalLink className="w-3 h-3" aria-hidden="true" />
            </a>
          )}

          <a
            href={paper.pdf_url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Open verified PDF for ${paper.title}`}
            className="button button--blue text-xs font-black uppercase px-3 py-1 border-2 border-black shadow-[3px_3px_0_#000000] inline-flex items-center gap-1.5 cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5" aria-hidden="true" />
            <span>VERIFIED PDF</span>
            <ExternalLink className="w-3 h-3 ml-0.5" aria-hidden="true" />
          </a>
        </div>
      </div>

      {/* Paper Title */}
      <h4 className="text-black font-black text-base uppercase leading-snug mt-3">
        {paper.title}
      </h4>

      {/* Authors and Published Date */}
      <div className="flex flex-wrap items-center gap-4 text-xs font-mono font-bold uppercase text-black mt-2.5">
        <div className="flex items-center gap-1.5">
          <Users className="w-3.5 h-3.5" aria-hidden="true" />
          <span>
            {paper.authors.slice(0, 3).join(", ")}
            {paper.authors.length > 3 ? " ET AL." : ""}
          </span>
        </div>
        {paper.published && (
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" aria-hidden="true" />
            <span>PUB: {paper.published}</span>
          </div>
        )}
      </div>

      {/* Abstract */}
      <p className="text-xs font-bold text-black mt-3 leading-relaxed bg-white p-3 border-2 border-black shadow-[3px_3px_0_#000000]">
        {paper.summary}
      </p>
    </div>
  );
};
