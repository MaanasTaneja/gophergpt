import React, { useState, useEffect } from "react";

const formatNumber = (value) => {
  if (value === null || value === undefined) return "N/A";
  return new Intl.NumberFormat("en-US").format(value);
};

const formatMetric = (value) => {
  if (value === null || value === undefined) return "N/A";
  return Number(value).toFixed(2);
};

const formatPercent = (value) => {
  if (value === null || value === undefined) return "N/A";
  return `${(value * 100).toFixed(1)}%`;
};

const formatCredits = (credits) => {
  if (!credits) return "N/A";
  const min = credits.min;
  const max = credits.max;
  if (min === null || min === undefined) return "N/A";
  if (max === null || max === undefined || min === max) return `${min}`;
  return `${min}-${max}`;
};

const getCourseLevel = (courseNum) => {
  const match = String(courseNum).match(/(\d+)/);
  if (!match) return "unknown";
  const num = parseInt(match[1]);
  if (num >= 8000) return "phd";
  if (num >= 5000) return "graduate";
  if (num >= 1000) return "undergraduate";
  return "unknown";
};

const getCourseGroup = (courseNum) => {
  const match = String(courseNum).match(/(\d+)/);
  if (!match) return null;
  const num = parseInt(match[1]);
  if (num < 2000) return 1;
  if (num < 3000) return 2;
  if (num < 4000) return 3;
  if (num < 5000) return 4;
  if (num < 6000) return 5;
  if (num < 7000) return 6;
  if (num < 8000) return 7;
  if (num < 9000) return 8;
  return 9;
};

const GROUP_META = {
  1: { label: "1000 Level", color: "text-blue-400",   border: "border-blue-900/40",   bg: "bg-blue-950/20" },
  2: { label: "2000 Level", color: "text-green-400",  border: "border-green-900/40",  bg: "bg-green-950/20" },
  3: { label: "3000 Level", color: "text-yellow-400", border: "border-yellow-900/40", bg: "bg-yellow-950/20" },
  4: { label: "4000 Level", color: "text-orange-400", border: "border-orange-900/40", bg: "bg-orange-950/20" },
  5: { label: "5000 Level", color: "text-purple-400", border: "border-purple-900/40", bg: "bg-purple-950/20" },
  6: { label: "6000 Level", color: "text-pink-400",   border: "border-pink-900/40",   bg: "bg-pink-950/20" },
  7: { label: "7000 Level", color: "text-rose-400",   border: "border-rose-900/40",   bg: "bg-rose-950/20" },
  8: { label: "8000 Level", color: "text-cyan-400",   border: "border-cyan-900/40",   bg: "bg-cyan-950/20" },
  9: { label: "9000 Level", color: "text-teal-400",   border: "border-teal-900/40",   bg: "bg-teal-950/20" },
};

// Which group keys belong to each tab
const LEVEL_GROUPS = {
  undergraduate: [1, 2, 3, 4],
  graduate:      [5, 6, 7],
  phd:           [8, 9],
  all:           [1, 2, 3, 4, 5, 6, 7, 8, 9],
};


const LEVEL_TABS = [
  { key: "all", label: "All Courses" },
  { key: "undergraduate", label: "Undergraduate" },
  { key: "graduate", label: "Graduate" },
  { key: "phd", label: "PhD" },
];

const INTRO_HINTS = ["introduction to", "intro to", "foundations", "fundamentals", "elementary", "principles", "basic "];

const KNOWN_REQUIRED_COURSES = {
  CSCI: new Set(["1133", "1913", "1933", "2011", "2021", "2033", "2041", "4041"]),
  MATH: new Set(["1271", "1272", "1371", "1372", "1571", "1572", "2243", "2263", "2373", "2374", "3283W"]),
  STAT: new Set(["3011", "3021", "3032", "5101"]),
  BIOL: new Set(["1951", "1961", "2003", "2004"]),
  CHEM: new Set(["1015", "1061", "1062", "2301", "2302"]),
  PHYS: new Set(["1301W", "1302W", "1401V", "1402V"]),
};

const computeFeatured = (courses, level, deptCode = "") => {
  const pool = level === "all" ? courses : courses.filter((c) => getCourseLevel(c.course_num) === level);

  const popular = [...pool]
    .sort((a, b) => (b.total_students ?? 0) - (a.total_students ?? 0))
    .slice(0, 8);

  const bestRated = [...pool]
    .filter((c) => (c.metrics.responses ?? 0) >= 50 && c.metrics.recommend != null)
    .sort((a, b) => b.metrics.recommend - a.metrics.recommend)
    .slice(0, 8);

  // Electives: upper-division courses, not required courses, not obviously intro
  const electivePool = pool.filter((c) => {
    const rawNum = String(c.course_num).trim();
    const match = rawNum.match(/(\d+)/);
    if (!match) return false;
    const num = parseInt(match[1]);
    const minLevel = level === "undergraduate" ? 3000 : level === "graduate" ? 5000 : level === "phd" ? 8000 : 3000;
    if (num < minLevel) return false;
    // Exclude known required courses for the dept
    const requiredSet = KNOWN_REQUIRED_COURSES[deptCode.toUpperCase()];
    if (requiredSet && requiredSet.has(rawNum)) return false;
    const combined = `${c.title} ${c.description || ""}`.toLowerCase();
    return !INTRO_HINTS.some((hint) => combined.includes(hint));
  });

  const popularElectives = [...electivePool]
    .sort((a, b) => (b.total_students ?? 0) - (a.total_students ?? 0))
    .slice(0, 8);

  return { popular, bestRated, popularElectives };
};

const SummaryCard = ({ label, value }) => (
  <div className="rounded-xl border border-[#4a1020] bg-[#1e0a10] p-4">
    <p className="text-xs uppercase tracking-wide text-[#a06070]">{label}</p>
    <p className="mt-2 text-2xl font-bold text-gold">{value}</p>
  </div>
);

const CourseRow = ({ course }) => (
  <tr className="border-b border-[#2a0d15] align-top hover:bg-[#1a0810] transition-colors">
    <td className="px-3 py-4 font-semibold text-gold">{course.course_num}</td>
    <td className="px-3 py-4">
      <div className="font-medium text-white">{course.title}</div>
      <div className="mt-1 max-w-xl text-xs leading-5 text-[#a06070]">
        {course.description
          ? `${course.description.slice(0, 160)}${course.description.length > 160 ? "..." : ""}`
          : "No description available."}
      </div>
      {course.catalog_url && (
        <a
          href={course.catalog_url}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-xs text-gold underline hover:text-[#ffd966]"
        >
          View Catalog Entry
        </a>
      )}
    </td>
    <td className="px-3 py-4 text-gray-300">{formatCredits(course.credits)}</td>
    <td className="px-3 py-4 text-gray-300">{formatNumber(course.total_students)}</td>
    <td className="px-3 py-4 text-gray-300">{formatMetric(course.metrics.recommend)}</td>
    <td className="px-3 py-4 text-gray-300">{formatNumber(course.metrics.responses)}</td>
    <td className="px-3 py-4 text-gray-300">{formatPercent(course.metrics.challenge_rate)}</td>
  </tr>
);

const CourseTableHead = () => (
  <thead className="border-b border-[#4a1020] text-[#a06070]">
    <tr>
      <th className="px-3 py-3 font-medium">Course</th>
      <th className="px-3 py-3 font-medium">Title</th>
      <th className="px-3 py-3 font-medium">Credits</th>
      <th className="px-3 py-3 font-medium">Students</th>
      <th className="px-3 py-3 font-medium">Recommend</th>
      <th className="px-3 py-3 font-medium">Responses</th>
      <th className="px-3 py-3 font-medium">Challenge</th>
    </tr>
  </thead>
);

const FeaturedList = ({ title, subtitle, items, metricLabel, renderMetric }) => (
  <div className="rounded-xl border border-[#4a1020] bg-[#1e0a10] p-4">
    <div className="mb-4">
      <h3 className="text-lg font-bold text-white">{title}</h3>
      <p className="text-sm text-[#a06070]">{subtitle}</p>
    </div>
    <div className="space-y-3">
      {items.map((course) => (
        <div key={`${title}-${course.id}`} className="rounded-lg border border-[#3a1018] bg-[#150709] p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-semibold text-gold">{course.course_num}</p>
              <p className="text-sm text-white">{course.title}</p>
            </div>
            <div className="text-right text-sm">
              <p className="text-[#a06070]">{metricLabel}</p>
              <p className="font-semibold text-white">{renderMetric(course)}</p>
            </div>
          </div>
          <p className="mt-2 text-xs text-[#7a3040]">
            {formatNumber(course.total_students)} students
          </p>
        </div>
      ))}
      {items.length === 0 && (
        <p className="text-sm text-[#a06070]">No courses matched this view.</p>
      )}
    </div>
  </div>
);

const DepartmentExplorer = () => {
  const [inputValue, setInputValue] = useState("");
  const [deptData, setDeptData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [filterText, setFilterText] = useState("");
  const [sortKey, setSortKey] = useState("total_students");
  const [sortDirection, setSortDirection] = useState("desc");
  const [activeLevel, setActiveLevel] = useState("all");
  const [collapsedYears, setCollapsedYears] = useState({});

  useEffect(() => {
    const userId = localStorage.getItem("gopher_user_id");
    if (!userId) return;
    fetch(`${process.env.REACT_APP_API_BASE}/profile?user_id=${encodeURIComponent(userId)}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.ok && data.profile?.level) {
          const l = data.profile.level.toLowerCase();
          if (l === "undergraduate" || l === "graduate" || l === "phd") {
            setActiveLevel(l);
          }
        }
      })
      .catch(() => {});
  }, []);

  const fetchDepartment = async () => {
    const dept = inputValue.trim();
    if (!dept || loading) return;
    setLoading(true);
    setError("");
    setDeptData(null);
    try {
      const response = await fetch(`${process.env.REACT_APP_API_BASE}/umn/dept`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dept }),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        setError(data.error || "Unable to load department data.");
        return;
      }
      setDeptData(data);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") fetchDepartment();
  };

  const applySort = (courses) =>
    [...courses].sort((a, b) => {
      if (sortKey === "course_num") {
        const cmp = a.course_num.localeCompare(b.course_num, undefined, { numeric: true, sensitivity: "base" });
        return sortDirection === "asc" ? cmp : -cmp;
      }
      let aVal = a[sortKey];
      let bVal = b[sortKey];
      if (sortKey === "recommend") { aVal = a.metrics.recommend ?? -1; bVal = b.metrics.recommend ?? -1; }
      else if (sortKey === "challenge_rate") { aVal = a.metrics.challenge_rate ?? -1; bVal = b.metrics.challenge_rate ?? -1; }
      if (aVal < bVal) return sortDirection === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

  const applyTextFilter = (courses) => {
    const query = filterText.trim().toLowerCase();
    if (!query) return courses;
    return courses.filter(
      (c) => c.course_num.toLowerCase().includes(query) || c.title.toLowerCase().includes(query)
    );
  };

  const filterByLevel = (courses, level) => {
    if (level === "all") return courses;
    return courses.filter((c) => getCourseLevel(c.course_num) === level);
  };

  const levelCounts = deptData
    ? {
        undergraduate: deptData.courses.filter((c) => getCourseLevel(c.course_num) === "undergraduate").length,
        graduate: deptData.courses.filter((c) => getCourseLevel(c.course_num) === "graduate").length,
        phd: deptData.courses.filter((c) => getCourseLevel(c.course_num) === "phd").length,
      }
    : {};

  const filteredSortedCourses = deptData
    ? applySort(applyTextFilter(filterByLevel(deptData.courses, activeLevel)))
    : [];

  // Group courses by level band for the active tab
  const levelGroups = (LEVEL_GROUPS[activeLevel] || []).map((group) => ({
    group,
    meta: GROUP_META[group],
    courses: filteredSortedCourses.filter((c) => getCourseGroup(c.course_num) === group),
  }));


  const featured = deptData ? computeFeatured(deptData.courses, activeLevel, deptData.dept.code) : { popular: [], bestRated: [], popularElectives: [] };

  return (
    <div className="flex-1 overflow-y-auto bg-dark-gray p-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">

        {/* Header */}
        <div>
          <h2 className="text-3xl font-bold text-white">Department Explorer</h2>
          <p className="mt-2 max-w-3xl text-sm text-[#a06070]">
            Explore a UMN department by course volume, grade patterns, and student ratings.
            Search by department code like CSCI, MATH, or STAT.
          </p>
        </div>

        {/* Search bar */}
        <div className="flex flex-col gap-3 rounded-xl border border-[#4a1020] bg-[#1e0a10] p-4 md:flex-row">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value.toUpperCase())}
            onKeyDown={handleKeyDown}
            placeholder="Enter department code (e.g. CSCI)"
            className="flex-1 rounded-lg border border-[#4a1020] bg-[#150709] p-3 text-white placeholder-[#7a3040] outline-none focus:border-gold/50"
          />
          <button
            onClick={fetchDepartment}
            disabled={loading}
            className="rounded-lg bg-gold px-6 py-3 font-semibold text-maroon disabled:cursor-not-allowed disabled:opacity-70 hover:bg-[#ffd966] transition-colors"
          >
            {loading ? "Loading..." : "Explore"}
          </button>
        </div>

        {error && (
          <div className="rounded-xl border border-[#7A0019] bg-[#2a0a10] p-4 text-sm text-red-200">
            {error}
          </div>
        )}

        {!deptData && !loading && !error && (
          <div className="rounded-xl border border-dashed border-[#4a1020] bg-[#1a0810]/60 p-8 text-center text-[#a06070]">
            Search for a department to see summary metrics, featured course views, and a sortable course explorer.
          </div>
        )}

        {deptData && (
          <>
            {/* Dept header + summary cards */}
            <div className="rounded-xl border border-[#4a1020] bg-gradient-to-br from-[#1e0a10] via-[#17080e] to-[#10050a] p-5">
              <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="text-sm uppercase tracking-wide text-[#a06070]">{deptData.dept.campus}</p>
                  <h3 className="text-2xl font-bold text-white">
                    {deptData.dept.name} <span className="text-gold">({deptData.dept.code})</span>
                  </h3>
                </div>
                <p className="text-sm text-[#7a3040]">
                  Ranked using historical GopherGrades distributions and SRT data.
                </p>
              </div>
              <div className="mt-5 grid gap-4 md:grid-cols-4">
                <SummaryCard label="Courses" value={formatNumber(deptData.summary.course_count)} />
                <SummaryCard label="Total Students" value={formatNumber(deptData.summary.total_students)} />
                <SummaryCard label="Median Size" value={formatNumber(deptData.summary.median_course_size)} />
                <SummaryCard label="Avg Recommend" value={formatMetric(deptData.summary.avg_recommend)} />
              </div>
            </div>

            {/* Level tabs */}
            <div className="flex flex-wrap gap-2">
              {LEVEL_TABS.map((tab) => {
                const count = tab.key === "all"
                  ? deptData.courses.length
                  : levelCounts[tab.key] ?? 0;
                const isActive = activeLevel === tab.key;
                return (
                  <button
                    key={tab.key}
                    onClick={() => setActiveLevel(tab.key)}
                    className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium border transition ${
                      isActive
                        ? "bg-gold text-[#1a0810] border-gold"
                        : "border-[#4a1020] text-[#a06070] hover:border-gold/40 hover:text-white"
                    }`}
                  >
                    {tab.label}
                    <span className={`rounded-full px-1.5 py-0.5 text-xs ${isActive ? "bg-[#1a0810]/30" : "bg-[#2a0d15] text-[#7a3040]"}`}>
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Featured lists (filtered by level) */}
            <div className="grid gap-4 xl:grid-cols-3">
              <FeaturedList
                title="Popular Courses"
                subtitle="Highest total enrollment."
                items={featured.popular}
                metricLabel="Students"
                renderMetric={(c) => formatNumber(c.total_students)}
              />
              <FeaturedList
                title="Best Rated"
                subtitle="Highest recommend scores with at least 50 responses."
                items={featured.bestRated}
                metricLabel="Recommend"
                renderMetric={(c) => formatMetric(c.metrics.recommend)}
              />
              <FeaturedList
                title="Popular Electives"
                subtitle="High-enrollment upper-division courses."
                items={featured.popularElectives}
                metricLabel="Students"
                renderMetric={(c) => formatNumber(c.total_students)}
              />
            </div>

            {/* Course Explorer */}
            <div className="rounded-xl border border-[#4a1020] bg-[#1e0a10] p-5">
              <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white">
                    {activeLevel === "undergraduate"
                      ? "Course Catalog"
                      : activeLevel === "graduate"
                      ? "Graduate Courses"
                      : activeLevel === "phd"
                      ? "PhD Courses"
                      : "Course Explorer"}
                  </h3>
                  <p className="text-sm text-[#a06070]">
                    {activeLevel === "undergraduate"
                      ? "Undergraduate courses grouped by level."
                      : activeLevel === "graduate"
                      ? "Graduate-level courses (5xxx–7xxx)."
                      : activeLevel === "phd"
                      ? "PhD-level courses (8xxx+)."
                      : "Full department catalog. Switch tabs to filter by academic level."}
                  </p>
                </div>

                <div className="flex flex-col gap-3 md:flex-row">
                  <input
                    type="text"
                    value={filterText}
                    onChange={(e) => setFilterText(e.target.value)}
                    placeholder="Filter by number or title"
                    className="rounded-lg border border-[#4a1020] bg-[#150709] p-2.5 text-white placeholder-[#7a3040] outline-none focus:border-gold/50"
                  />
                  <select
                    value={sortKey}
                    onChange={(e) => setSortKey(e.target.value)}
                    className="rounded-lg border border-[#4a1020] bg-[#150709] p-2.5 text-white outline-none"
                  >
                    <option value="total_students">Students</option>
                    <option value="course_num">Course Number</option>
                    <option value="recommend">Recommend</option>
                    <option value="challenge_rate">Challenge Rate</option>
                  </select>
                  <select
                    value={sortDirection}
                    onChange={(e) => setSortDirection(e.target.value)}
                    className="rounded-lg border border-[#4a1020] bg-[#150709] p-2.5 text-white outline-none"
                  >
                    <option value="desc">Descending</option>
                    <option value="asc">Ascending</option>
                  </select>
                </div>
              </div>

              {/* Grouped collapsible sections for all levels */}
              <div className="flex flex-col gap-3">
                {levelGroups.map(({ group, meta, courses }) =>
                  courses.length === 0 ? null : (
                    <div key={group}>
                      <button
                        onClick={() => setCollapsedYears((prev) => ({ ...prev, [group]: !prev[group] }))}
                        className={`w-full flex items-center gap-3 rounded-lg border ${meta.border} ${meta.bg} px-4 py-2.5 text-left transition hover:brightness-110`}
                      >
                        <span className={`text-sm font-bold ${meta.color}`}>{meta.label}</span>
                        <span className="text-xs text-gray-500">{courses.length} courses</span>
                        <span className="ml-auto text-xs text-gray-400">
                          {collapsedYears[group] ? "▶ Show" : "▼ Hide"}
                        </span>
                      </button>
                      {!collapsedYears[group] && (
                        <div className="overflow-x-auto mt-1">
                          <table className="min-w-full text-left text-sm">
                            <CourseTableHead />
                            <tbody>
                              {courses.map((course) => <CourseRow key={course.id} course={course} />)}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )
                )}
                {filteredSortedCourses.length === 0 && (
                  <p className="text-sm text-[#a06070]">No courses matched your current filter.</p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DepartmentExplorer;
