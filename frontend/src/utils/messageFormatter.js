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

function splitIntoBulletPoints(text) {
    return text
        .split(/(?:\.\s+|;\s+|\n+)/)
        .map((part) => part.trim())
        .filter(Boolean);
}

function wrapSection(content, className = "response-section") {
    return `<section class="${className}">${content}</section>`;
}

// Safely process a line: boldify and linkify before escaping using placeholder tokens,
// then escape, restore HTML, then linkify remaining raw URLs
export function processLine(text) {

    const cleaned = text.replace(/\*\*\s*\*\*/g, "").replace(/\*\*\s*$/g, "").trim();

    const bolded = cleaned.replace(/\*\*\s*(.*?)\s*\*\*/g, "\x00BOLD_START\x00$1\x00BOLD_END\x00");

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

function isLocationHeading(text) {
    const trimmed = text.trim();

    if (!trimmed || trimmed.length > 90) {
        return false;
    }

    if (!/[A-Za-z]/.test(trimmed) || /[.?!]$/.test(trimmed)) {
        return false;
    }

    return /(?:library|hall|union|center|centre|building|plaza|mall|commons|cafe|caf[ée]|bridge|park|lounge|lab|room|museum|rec|recreation|study|campus|quadrangle|quad)$/i.test(trimmed)
        || /^(?:northrop|coffman|walter|wilson|bruininks|lind|keller|appleby|tate|folwell|magrath|mccarthy|pillsbury|weisman)\b/i.test(trimmed);
}

function tryFormatLocationSections(raw) {
    const lines = String(raw).split(/\r?\n/);
    const parts = [];
    let index = 0;
    let foundSection = false;

    while (index < lines.length) {
        const current = lines[index].trim();

        if (!current) {
            index += 1;
            continue;
        }

        const headingMatch = current.match(/^(?:\d+\.\s+)?(?:\*\*)?([^:]+?)(?:\*\*)?:\s*(.*)$/);
        const title = headingMatch?.[1]?.trim();

        if (!title || !isLocationHeading(title)) {
            parts.push(wrapSection(`<p>${processLine(current)}</p>`));
            index += 1;
            continue;
        }

        foundSection = true;
        const bulletPoints = [];
        const inlineDescription = headingMatch[2]?.trim();

        if (inlineDescription) {
            bulletPoints.push(...splitIntoBulletPoints(inlineDescription));
        }

        index += 1;

        while (index < lines.length) {
            const nextLine = lines[index].trim();

            if (!nextLine) {
                index += 1;
                break;
            }

            if (/^(?:\d+\.\s+)?(?:\*\*)?[^:]+(?:\*\*)?:\s*/.test(nextLine)) {
                break;
            }

            const existingBulletMatch = nextLine.match(/^[-*\u2022]\s+(.*)$/);
            if (existingBulletMatch) {
                bulletPoints.push(existingBulletMatch[1].trim());
            } else {
                bulletPoints.push(...splitIntoBulletPoints(nextLine));
            }

            index += 1;
        }

        const normalizedBullets = bulletPoints.filter(Boolean);
        const bulletMarkup = normalizedBullets.length
            ? `<ul>${normalizedBullets.map((item) => `<li>${processLine(item)}</li>`).join("")}</ul>`
            : "";

        parts.push(
            wrapSection(
                `<p class="location-title"><strong>${processLine(title)}</strong></p>${bulletMarkup}`,
                "response-section location-section"
            )
        );
    }

    return foundSection ? parts.join("") : null;
}

export function formatBotMessage(raw) {
    const locationMarkup = tryFormatLocationSections(raw);
    if (locationMarkup) {
        return locationMarkup;
    }

    // Convert raw text into safe, readable HTML with lists and headings
    const lines = String(raw).split(/\r?\n/);
    const parts = [];
    let activeListType = null;
    let activeListItems = [];

    const flushLists = () => {
        if (!activeListType) {
            return;
        }

        const listTag = activeListType === "ol" ? "ol" : "ul";
        parts.push(wrapSection(`<${listTag}>${activeListItems.join("")}</${listTag}>`));
        activeListType = null;
        activeListItems = [];
    };

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        if (!line) {
            flushLists();
            continue;
        }

        // Ordered list item: starts with '1. ' or '2) '
        const olMatch = line.match(/^\d+\s*[\.|\)]\s*(.*)$/);
        if (olMatch) {
            if (activeListType !== "ol") {
                flushLists();
                activeListType = "ol";
            }
            const content = olMatch[1];
            // If content has a title-like part ending with ':' separate it
            const titleMatch = content.match(/^(.*?:)\s*(.*)$/);
            if (titleMatch) {
                const title = titleMatch[1];
                const rest = titleMatch[2];
                activeListItems.push(`<li><strong>${processLine(title)}</strong> ${processLine(rest)}</li>`);
            } else {
                activeListItems.push(`<li>${processLine(content)}</li>`);
            }
            continue;
        }

        // Unordered list item: starts with -, *, or •
        const ulMatch = line.match(/^[-\*\u2022]\s+(.*)$/);
        if (ulMatch) {
            if (activeListType !== "ul") {
                flushLists();
                activeListType = "ul";
            }
            const content = ulMatch[1];
            activeListItems.push(`<li>${processLine(content)}</li>`);
            continue;
        }

        // Markdown headings: ###, ##, #
        const headingMatch = line.match(/^(#{1,3})\s+(.*)$/);
        if (headingMatch) {
            flushLists();
            const content = headingMatch[2];
            parts.push(wrapSection(`<p class="response-heading"><strong>${processLine(content)}</strong></p>`));
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
            parts.push(wrapSection(`<p class="response-heading">${processLine(line)}</p>`));
            continue;
        }

        // Default paragraph
        flushLists();
        parts.push(wrapSection(`<p>${processLine(line)}</p>`));
    }

    flushLists();
    return parts.join("");
}
