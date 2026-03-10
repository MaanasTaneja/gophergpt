export function getLoadingLabel(userText) {

    const t = userText.toLowerCase();

    // if we want to widen the search parameter, copy format below:

    // searching for keywords
    if (/\bcanvas\b/.test(t)) return "Checking Canvas";
    if (/\bcsci\b/.test(t)) return "Searching course catalog";
    if (/\bcoffman\b/.test(t) || /\bnorthrup\b/.test(t)) /* add more buildings */
    return "Looking up building info";

    return "Thinking";
}

/* 
Note: This file should include the function loadingLabel

The function has been hardcoded to filter for keywords, instead of patterns, so loading label may appear incorrect, depending on the prompt.

Would like to find a way to make this more flexible, instead of hardcoded.
*/