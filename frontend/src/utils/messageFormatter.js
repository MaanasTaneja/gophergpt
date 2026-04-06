export function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function processInline(text) {
    // 1. Protect markdown links before escaping
    const LINKS = [];
    let t = text.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, (_, label, url) => {
        const i = LINKS.length;
        LINKS.push({ label, url });
        return `\x00LINK${i}\x00`;
    });

    // 2. Protect bold spans
    const BOLDS = [];
    t = t.replace(/\*\*(.*?)\*\*/g, (_, inner) => {
        const i = BOLDS.length;
        BOLDS.push(inner);
        return `\x00BOLD${i}\x00`;
    });

    // 3. Escape HTML
    t = escapeHtml(t);

    // 4. Restore bold
    t = t.replace(/\x00BOLD(\d+)\x00/g, (_, i) =>
        `<strong>${escapeHtml(BOLDS[i])}</strong>`
    );

    // 5. Restore markdown links
    t = t.replace(/\x00LINK(\d+)\x00/g, (_, i) => {
        const { label, url } = LINKS[i];
        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
    });

    // 6. Auto-linkify bare URLs not already in an href
    t = t.replace(/(?<!href=")(?<!">)(https?:\/\/[^\s<>"]+)/g, (url) => {
        const m = url.match(/^(.*?)([)\].,;:!?]*)$/);
        const clean = m ? m[1] : url;
        const trail = m ? m[2] : "";
        return `<a href="${clean}" target="_blank" rel="noopener noreferrer">${clean}</a>${trail}`;
    });

    return t;
}

function normalizeLine(line) {
    // Fix unclosed ** at start: **Name → **Name**
    const openCount = (line.match(/\*\*/g) || []).length;
    if (openCount % 2 !== 0) {
        // Odd number of ** — close the last one
        if (line.startsWith("**") && openCount === 1) {
            line = line + "**";
        }
    }
    return line;
}

export function formatBotMessage(raw) {
    const lines = String(raw).split(/\r?\n/);
    const parts = [];
    let inOl = false;
    let inUl = false;
    let olCounter = 0; // tracks position across list breaks so numbering is continuous

    const flushLists = () => {
        if (inOl) { parts.push("</ol>"); inOl = false; }
        if (inUl) { parts.push("</ul>"); inUl = false; }
    };

    for (let i = 0; i < lines.length; i++) {
        let line = normalizeLine(lines[i].trim());

        // Blank line → spacer
        if (!line) {
            flushLists();
            parts.push('<div class="msg-gap"></div>');
            continue;
        }

        // Markdown headings: ###, ##, #
        const hMatch = line.match(/^(#{1,3})\s+(.+)$/);
        if (hMatch) {
            flushLists();
            olCounter = 0;
            const level = hMatch[1].length;
            const cls = level === 1 ? "msg-h1" : level === 2 ? "msg-h2" : "msg-h3";
            parts.push(`<div class="${cls}">${processInline(hMatch[2])}</div>`);
            continue;
        }

        // Ordered list: "1. " or "1) "
        const olMatch = line.match(/^\d+[\.\)]\s+(.+)$/);
        if (olMatch) {
            if (!inOl) {
                flushLists();
                // start attribute continues numbering if we were already counting
                const start = olCounter + 1;
                parts.push(`<ol class="msg-ol" start="${start}">`);
                inOl = true;
            }
            olCounter++;
            parts.push(`<li>${processInline(olMatch[1])}</li>`);
            continue;
        }

        // Unordered list: "- ", "* ", "• "
        const ulMatch = line.match(/^[-*\u2022]\s+(.+)$/);
        if (ulMatch) {
            const content = ulMatch[1];
            // Bullet whose entire content is bold text → treat as section heading
            const boldHeader = content.match(/^\*\*(.+?)\*\*:?\s*$/);
            if (boldHeader) {
                flushLists();
                olCounter = 0;
                parts.push(`<div class="msg-section">${escapeHtml(boldHeader[1])}</div>`);
                continue;
            }
            if (!inUl) { flushLists(); parts.push('<ul class="msg-ul">'); inUl = true; }
            parts.push(`<li>${processInline(content)}</li>`);
            continue;
        }

        flushLists();

        // Bold-only line (section heading): **Some Title** or **Some Title:**
        const boldOnly = line.match(/^\*\*(.+?)\*\*:?\s*$/);
        if (boldOnly) {
            olCounter = 0;
            parts.push(`<div class="msg-section">${escapeHtml(boldOnly[1])}</div>`);
            continue;
        }

        // Regular paragraph
        parts.push(`<p class="msg-p">${processInline(line)}</p>`);
    }

    flushLists();
    return parts.join("");
}
