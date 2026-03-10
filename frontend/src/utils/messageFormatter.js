/* 

Note: This file should include the function escapeHtml, linkify, boldify, and formatBotMessage.
Essentially anything regarding message formatting.

This file should include all functions that format the message (formatBotMessage, escapeHtml, boldify, linkify, etc).

*/


// Basic client-side formatter for bot messages (no external deps)
// - escape HTML
// - convert **bold** markers to <strong>
// - auto-link URLs
// - preserve newlines as <br>
export function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}


export function linkify(text) {
    // Simple URL regex (http/https)
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.replace(urlRegex, (url) => {
        // If the URL is followed by closing punctuation (common in parentheses or end-of-sentence),
        // trim those characters out of the href and append them after the anchor.
        const m = url.match(/^(.*?)([)\].,;:!?]*)$/);
        const clean = m ? m[1] : url;
        const trailing = m ? m[2] : "";
        return `<a class="text-gold underline" href="${clean}" target="_blank" rel="noopener noreferrer">${clean}</a>${trailing}`;
    });
}

export function boldify(text) {
    // Replace **bold** with <strong>
    return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
}

export function formatBotMessage(raw) {
    // Convert raw text into safe, readable HTML with lists and headings
    const lines = String(raw).split(/\r?\n/);
    const parts = [];
    let inOl = false;
    let inUl = false;

    const flushLists = () => {
        if (inOl) {
        parts.push("</ol>");
        inOl = false;
        }
        if (inUl) {
        parts.push("</ul>");
        inUl = false;
        }
    };

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        if (!line) {
        // blank line -> paragraph break
        flushLists();
        parts.push("<p></p>");
        continue;
        }

        // Ordered list item: starts with '1. ' or '2) '
        const olMatch = line.match(/^\d+\s*[\.|\)]\s*(.*)$/);
        if (olMatch) {
        if (!inOl) {
            flushLists();
            parts.push("<ol>");
            inOl = true;
        }
        const content = olMatch[1];
        // If content has a title-like part ending with ':' separate it
        const titleMatch = content.match(/^(.*?:)\s*(.*)$/);
        if (titleMatch) {
            const title = titleMatch[1];
            const rest = titleMatch[2];
            const html = linkify(boldify(escapeHtml(rest)));
            parts.push(`<li><strong>${escapeHtml(title)}</strong> ${html}</li>`);
        } else {
            const html = linkify(boldify(escapeHtml(content)));
            parts.push(`<li>${html}</li>`);
        }
        continue;
        }

        // Unordered list item: starts with -, *, or •
        const ulMatch = line.match(/^[-\*\u2022]\s+(.*)$/);
        if (ulMatch) {
        if (!inUl) {
            flushLists();
            parts.push("<ul>");
            inUl = true;
        }
        const content = ulMatch[1];
        const html = linkify(boldify(escapeHtml(content)));
        parts.push(`<li>${html}</li>`);
        continue;
        }

        // Heading-like: line that ends with ':' or is short and in ALL CAPS -> bold
        if (
        /[:]\s*$/.test(line) ||
        (line.length < 60 && line === line.toUpperCase())
        ) {
        flushLists();
        parts.push(`<p><strong>${escapeHtml(line)}</strong></p>`);
        continue;
        }

        // Default paragraph
        flushLists();
        const html = linkify(boldify(escapeHtml(line)));
        parts.push(`<p>${html}</p>`);
    }

    flushLists();
    // Join parts and collapse adjacent empty paragraphs
    return parts.join("").replace(/<p><\/p><p><\/p>/g, "<p></p>");
}