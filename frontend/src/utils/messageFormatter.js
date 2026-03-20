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
    // Negative lookbehind skips URLs already inside href attributes
    const urlRegex = /(?<!href=")(https?:\/\/[^\s<>"]+)/g;
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
    // Replace **bold** with <strong>, trim inner whitespace
    return text.replace(/\*\*\s*(.*?)\s*\*\*/g, "<strong>$1</strong>");
}

// Safely process a line: boldify and linkify before escaping using placeholder tokens,
// then escape, restore HTML, then linkify remaining raw URLs
export function processLine(text) {

    const cleaned = text.replace(/\*\*\s*\*\*/g, "").trim();

    const bolded = text.replace(/\*\*\s*(.*?)\s*\*\*/g, "\x00BOLD_START\x00$1\x00BOLD_END\x00");

    const linkedMd = bolded.replace(
        /\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g,
        "\x00LINK_START\x00$2\x00LINK_MID\x00$1\x00LINK_END\x00"
    );

    const escaped = escapeHtml(linkedMd);

    const restored = escaped
        .replace(/\x00BOLD_START\x00/g, "<strong>")
        .replace(/\x00BOLD_END\x00/g, "</strong>")
        .replace(
            /\x00LINK_START\x00(.*?)\x00LINK_MID\x00(.*?)\x00LINK_END\x00/g,
            `<a class="text-gold underline" href="$1" target="_blank" rel="noopener noreferrer">$2</a>`
        );

        return linkify(restored);
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
                parts.push(`<li><strong>${processLine(title)}</strong> ${processLine(rest)}</li>`);
            } else {
                parts.push(`<li>${processLine(content)}</li>`);
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
            parts.push(`<li>${processLine(content)}</li>`);
            continue;
        }

        // Markdown headings: ###, ##, #
        const headingMatch = line.match(/^(#{1,3})\s+(.*)$/);
        if (headingMatch) {
            flushLists();
            const content = headingMatch[2];
            parts.push(`<p><strong>${processLine(content)}</strong></p>`);
            continue;
        }

        // Heading-like: line that ends with ':' or is short and in ALL CAPS -> bold
        // Use strippedLine for detection only, process original line for output
        const strippedLine = line.replace(/\*\*\s*(.*?)\s*\*\*/g, "$1");
        if (
            /[:]\s*$/.test(strippedLine) ||
            (strippedLine.length < 60 && strippedLine === strippedLine.toUpperCase())
        ) {
            flushLists();
            parts.push(`<p>${processLine(line)}</p>`);
            continue;
        }

        // Default paragraph
        flushLists();
        parts.push(`<p>${processLine(line)}</p>`);
    }

    flushLists();
    // Join parts and collapse adjacent empty paragraphs
    return parts.join("").replace(/<p><\/p><p><\/p>/g, "<p></p>");
}