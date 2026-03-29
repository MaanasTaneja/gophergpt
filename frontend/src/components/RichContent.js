import React from "react";

function shorten(text, max = 220) {
    if (!text) return "";
    const cleaned = String(text).replace(/\s+/g, " ").trim();
    return cleaned.length > max ? `${cleaned.slice(0, max).trim()}...` : cleaned;
}

function ResearchCard({ item }) {
    const results = Array.isArray(item.results) ? item.results.slice(0, 4) : [];
    const summary = shorten(item.summary, 280);

    return (
        <div className="mt-4 overflow-hidden rounded-2xl border border-gold/20 bg-gradient-to-br from-[#20252f] via-[#1a1f28] to-[#141922] shadow-[0_18px_50px_rgba(0,0,0,0.35)]">
            <div className="border-b border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(255,204,51,0.16),_transparent_38%)] px-5 py-5">
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <p className="text-[11px] uppercase tracking-[0.28em] text-gold/80">
                            Research Explorer
                        </p>
                        <h3 className="mt-2 text-2xl font-semibold leading-tight text-white">
                            UMN Research Snapshot
                        </h3>
                    </div>
                    <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-gray-300">
                        {results.length} result{results.length === 1 ? "" : "s"}
                    </div>
                </div>

                {summary && (
                    <p className="mt-4 max-w-4xl text-sm leading-7 text-gray-300">
                        {summary}
                    </p>
                )}
            </div>

            <div className="grid gap-4 p-5">
                {results.map((result, index) => (
                    <a
                        key={`${result.url || result.title}-${index}`}
                        href={result.url}
                        target="_blank"
                        rel="noreferrer"
                        className="group block rounded-xl border border-white/8 bg-white/[0.03] p-4 transition duration-200 hover:border-gold/40 hover:bg-white/[0.06]"
                    >
                        <div className="flex items-start justify-between gap-4">
                            <div className="min-w-0">
                                <h4 className="text-lg font-semibold leading-snug text-gold transition group-hover:text-[#ffd966]">
                                    {shorten(result.title, 88) || "Untitled result"}
                                </h4>
                                <p className="mt-2 text-sm leading-6 text-gray-300">
                                    {shorten(result.snippet, 180)}
                                </p>
                                {result.url && (
                                    <p className="mt-3 truncate text-xs uppercase tracking-[0.18em] text-gray-500">
                                        {result.url.replace(/^https?:\/\//, "")}
                                    </p>
                                )}
                            </div>

                            <div className="hidden rounded-full border border-gold/20 bg-gold/10 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-gold md:block">
                                Open
                            </div>
                        </div>
                    </a>
                ))}
            </div>
        </div>
    );
}

export default function RichContent({ content = [] }) {
    if (!content.length) return null;

    return (
        <div className="space-y-4">
            {content.map((item, index) => {
                if (item.type === "research") {
                    return <ResearchCard key={index} item={item} />;
                }

                return null;
            })}
        </div>
    );
}
