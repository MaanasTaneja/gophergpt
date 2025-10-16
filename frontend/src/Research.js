import React, { useState } from 'react';
import './App.css';

export default function Research() {
    const [query, setQuery] = useState('Climate change adaptation');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState([]);
    const [summary, setSummary] = useState(null);
    const [error, setError] = useState(null);

    const runSearch = async () => {
        setLoading(true);
        setError(null);
        setResults([]);

        try {
            // Use the same explicit backend URL style as `App.js` so requests go directly
            // to the FastAPI backend instead of being proxied by the frontend server.
            // Ensure the keyword 'research' is included so users don't have to type it
            let outQuery = (query || '').trim();
            if (!/\bresearch\b/i.test(outQuery)) {
                outQuery = outQuery + ' research';
            }

            const res = await fetch('http://localhost:8000/research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: outQuery, max_results: 5 }),
            });

            const contentType = res.headers.get('content-type') || '';
            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            if (contentType.includes('application/json')) {
                const data = await res.json();

                // helper: detect dump-like provider lines
                const looksLikeDump = (s) => {
                    if (!s) return false;
                    const low = s.toLowerCase();
                    return low.includes("'query'") || low.includes("'results'") || low.includes("'images'") || low.trim().startsWith('{');
                }

                // sanitize and filter results so users don't see provider raw dumps
                const rawResults = data.results || [];
                let cleaned = rawResults.filter(r => {
                    const snip = r?.snippet || '';
                    const title = r?.title || '';
                    // skip if snippet or title looks like a provider dump
                    if (looksLikeDump(snip) || looksLikeDump(title)) return false;
                    // skip if snippet is very short or empty
                    if (!snip || snip.trim().length < 8) return false;
                    return true;
                }).map(r => ({
                    title: (r.title || r.url || '').toString(),
                    url: (r.url || '').toString(),
                    snippet: (r.snippet || '').toString(),
                }));

                // If filtering removed everything, fall back to sanitized raw results (title + url + short snippet)
                if (cleaned.length === 0 && rawResults.length > 0) {
                    cleaned = rawResults.map(r => {
                        const title = (r?.title || r?.url || 'Result').toString();
                        let snippet = (r?.snippet || r?.content || '').toString();
                        if (looksLikeDump(snippet) || snippet.trim().length < 10) snippet = '';
                        if (snippet.length > 180) snippet = snippet.slice(0, 177).trim() + '...';
                        return { title, url: (r?.url || '').toString(), snippet };
                    });
                }

                // sanitize summary: remove any lines that look like dumps; if empty, build a short header + list from cleaned
                const rawSummary = data.summary || '';
                const sanitizeSummary = (s) => {
                    if (!s) return '';
                    const lines = s.split(/\n/).map(l => l.trim()).filter(Boolean);
                    const kept = lines.filter(l => !looksLikeDump(l));
                    // If everything was removed, fall back to a generated list from cleaned results
                    if (kept.length === 0) {
                        if (!cleaned || cleaned.length === 0) return '';
                        const header = `Found ${cleaned.length} result${cleaned.length!==1? 's':''}:`;
                        const items = cleaned.map((c, i) => `${i+1}. ${c.title}\n   Link: ${c.url}`);
                        return header + '\n\n' + items.join('\n\n');
                    }
                    return kept.join('\n\n');
                }

                setResults(cleaned);
                const sanitized = sanitizeSummary(rawSummary);
                setSummary(sanitized || null);
            } else {
                const text = await res.text();
                setError('Server did not return JSON. Response preview:\n' + text.slice(0, 1000));
            }
        } catch (err) {
            setError(String(err));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 max-w-3xl mx-auto">
            <h2 className="text-2xl font-bold mb-4">UMN Research Finder</h2>
            <p className="mb-4 text-sm text-gray-300">Search UMN domains and get short snippets of results. Uses TavilySearch + OpenAI for summarization when configured.</p>

            <div className="mb-4">
                <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="w-full p-2 rounded bg-gray-800 border border-gray-700"
                    placeholder="Enter a research query"
                />
            </div>

            <div className="flex items-center space-x-2 mb-6">
                <button onClick={runSearch} disabled={loading} className="px-4 py-2 bg-gold text-maroon rounded">
                    {loading ? 'Searching...' : 'Run Search'}
                </button>
            </div>

            {error && (
                <div className="bg-red-900 p-3 rounded mb-4 whitespace-pre-wrap">{error}</div>
            )}

            {/* Summary (if provided by backend) */}
            {summary && (
                <div className="p-4 mb-4 bg-gray-800 border-l-4 border-gold rounded">
                    <div className="text-sm text-gray-200 font-semibold">Summary</div>
                    <div className="text-sm text-gray-300 mt-2" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>{summary}</div>
                </div>
            )}

            <div className="space-y-4">
                {results.map((r, i) => (
                    <div key={i} className="p-3 border border-gray-700 rounded bg-gray-900">
                        <a href={r.url} className="text-gold font-semibold" target="_blank" rel="noreferrer">{r.title || r.url}</a>
                        <div className="text-sm text-gray-300 mt-1">{r.snippet}</div>
                        <div className="text-xs text-gray-500 mt-2">{r.url}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}
