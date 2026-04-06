import React from "react";
import GradeChart from "./compare/GradeChart";
import SRTRatings from "./compare/SRTRatings";

function shorten(text, max = 220) {
    if (!text) return "";
    const cleaned = String(text).replace(/\s+/g, " ").trim();
    return cleaned.length > max ? `${cleaned.slice(0, max).trim()}...` : cleaned;
}

function ResearchCard({ item }) {
    const results = Array.isArray(item.results) ? item.results.slice(0, 4) : [];
    const summary = shorten(item.summary, 280);

    return (
        <div className="mt-4 rounded-2xl border border-[#4a1020] bg-gradient-to-br from-[#1e0a10] via-[#17080e] to-[#10050a] shadow-[0_18px_50px_rgba(122,0,25,0.25)]">
            {/* Header */}
            <div className="border-b border-[#4a1020] bg-[radial-gradient(circle_at_top_left,_rgba(122,0,25,0.25),_transparent_42%)] px-5 py-5 rounded-t-2xl overflow-hidden">
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <p className="text-[11px] uppercase tracking-[0.28em] text-gold/80">
                            Research Explorer
                        </p>
                        <h3 className="mt-2 text-2xl font-semibold leading-tight text-white">
                            UMN Research Snapshot
                        </h3>
                    </div>
                    <div className="rounded-full border border-[#4a1020] bg-[#2a0d15] px-3 py-1 text-xs text-gray-300">
                        {results.length} result{results.length === 1 ? "" : "s"}
                    </div>
                </div>

                {summary && (
                    <p className="mt-4 max-w-4xl text-sm leading-7 text-gray-300">
                        {summary}
                    </p>
                )}
            </div>

            {/* Results */}
            <div className="grid gap-3 p-5">
                {results.map((result, index) => (
                    <a
                        key={`${result.url || result.title}-${index}`}
                        href={result.url}
                        target="_blank"
                        rel="noreferrer"
                        className="group block rounded-xl border border-[#3a1018] bg-[#1a0810] p-4 transition duration-200 hover:border-gold/40 hover:bg-[#250e18]"
                    >
                        <div className="flex items-start justify-between gap-4">
                            <div className="min-w-0">
                                <h4 className="text-base font-semibold leading-snug text-gold transition group-hover:text-[#ffd966]">
                                    {shorten(result.title, 88) || "Untitled result"}
                                </h4>
                                <p className="mt-2 text-sm leading-6 text-gray-300">
                                    {shorten(result.snippet, 180)}
                                </p>
                                {result.url && (
                                    <p className="mt-2 truncate text-xs uppercase tracking-[0.15em] text-[#7a3040]">
                                        {result.url.replace(/^https?:\/\//, "")}
                                    </p>
                                )}
                            </div>
                            <div className="hidden shrink-0 rounded-full border border-gold/30 bg-[#3a1020] px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-gold md:block">
                                Open
                            </div>
                        </div>
                    </a>
                ))}
            </div>
        </div>
    );
}

function CourseCompareCard({ item }) {
    const courses = Array.isArray(item.courses) ? item.courses : [];
    const summary = item.summary || "";

    return (
        <div className="mt-4 overflow-hidden rounded-2xl border border-[#4a1020] bg-gradient-to-br from-[#1e0a10] via-[#17080e] to-[#10050a] shadow-[0_18px_50px_rgba(122,0,25,0.25)]">
            {/* Header */}
            <div className="border-b border-[#4a1020] bg-[radial-gradient(circle_at_top_left,_rgba(122,0,25,0.25),_transparent_42%)] px-5 py-5">
                <p className="text-[11px] uppercase tracking-[0.28em] text-gold/80">Course Compare</p>
                <h3 className="mt-2 text-2xl font-semibold leading-tight text-white">
                    {courses.map(c => c.code).join(" vs ")}
                </h3>
                {summary && (
                    <p className="mt-4 max-w-4xl text-sm leading-7 text-gray-300">{summary}</p>
                )}
            </div>

            {/* Panels */}
            <div className={`grid gap-6 p-5 ${courses.length >= 2 ? "grid-cols-1 lg:grid-cols-2" : "grid-cols-1"}`}>
                {courses.map((course) => (
                    <div key={course.code} className="rounded-xl border border-[#3a1018] bg-[#1a0810] p-4">
                        <h4 className="text-lg font-bold text-gold mb-4">{course.code}</h4>
                        {course.data?.total_grades && (
                            <GradeChart grades={course.data.total_grades} />
                        )}
                        {course.data?.srt_vals && (
                            <div className="mt-6">
                                <SRTRatings srtVals={course.data.srt_vals} />
                            </div>
                        )}
                    </div>
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
                if (item.type === "research") return <ResearchCard key={index} item={item} />;
                if (item.type === "compare") return <CourseCompareCard key={index} item={item} />;
                return null;
            })}
        </div>
    );
}
