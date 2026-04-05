export function getLoadingLabel(userText) {
    const t = userText.toLowerCase();

    // Research
    if (/\bresearch\b/.test(t)) return "Searching UMN research";

    // Course comparison
    if (/\bcompar(e|ing)\b/.test(t)) return "Comparing courses";

    // Professor queries
    if (/\bprofessor\b|\bprof\b|\binstructor\b|\bteacher\b/.test(t)) return "Looking up professor";

    // Department queries
    if (/\bdepartment\b|\bdept\b/.test(t)) return "Loading department data";

    // Specific course code (e.g. CSCI 4041, MATH1271)
    if (/\b[a-z]{2,6}\s*\d{4}\b/.test(t)) return "Fetching course data";

    // Known departments by abbreviation
    if (/\bcsci\b|\bcs\b/.test(t)) return "Searching Computer Science";
    if (/\bmath\b/.test(t)) return "Searching Mathematics";
    if (/\bbiol\b|\bbiology\b/.test(t)) return "Searching Biology";
    if (/\bpsy\b|\bpsych\b|\bpsychology\b/.test(t)) return "Searching Psychology";
    if (/\bphys\b|\bphysics\b/.test(t)) return "Searching Physics";
    if (/\bchem\b|\bchemistry\b/.test(t)) return "Searching Chemistry";
    if (/\becon\b|\beconomics\b/.test(t)) return "Searching Economics";
    if (/\bengl\b|\benglish\b/.test(t)) return "Searching English";
    if (/\bhist\b|\bhistory\b/.test(t)) return "Searching History";
    if (/\bsoc\b|\bsociology\b/.test(t)) return "Searching Sociology";
    if (/\bstat\b|\bstatistics\b/.test(t)) return "Searching Statistics";

    // GPA / grades / difficulty
    if (/\bgpa\b|\bgrade(s)?\b|\bdifficult\b|\bhard\b|\beasy\b/.test(t)) return "Analyzing grade data";

    // Campus locations
    if (/\bcoffman\b|\bnorthrup\b|\bwilley\b|\bkeller\b|\bnolte\b|\bwilson\b/.test(t)) return "Looking up campus info";
    if (/\blibrary\b|\blab\b|\bbuilding\b/.test(t)) return "Looking up campus info";

    // Canvas / online tools
    if (/\bcanvas\b/.test(t)) return "Checking Canvas info";

    // Schedule / registration
    if (/\bschedule\b|\bregister\b|\bregistration\b|\benroll\b/.test(t)) return "Checking schedule info";

    // Housing / dining
    if (/\bhousing\b|\bdining\b|\bdorm\b|\bfood\b/.test(t)) return "Looking up campus resources";

    return "Thinking";
}
