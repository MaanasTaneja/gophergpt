import React, { useState } from "react";

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

const SummaryCard = ({ label, value }) => (
  <div className="rounded-xl border border-[#4a1020] bg-[#1e0a10] p-4">
    <p className="text-xs uppercase tracking-wide text-[#a06070]">{label}</p>
    <p className="mt-2 text-2xl font-bold text-gold">{value}</p>
  </div>
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
    } catch (err) {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") fetchDepartment();
  };

  const displayedCourses = deptData
    ? [...deptData.courses]
        .filter((course) => {
          const query = filterText.trim().toLowerCase();
          if (!query) return true;
          return (
            course.course_num.toLowerCase().includes(query) ||
            course.title.toLowerCase().includes(query)
          );
        })
        .sort((a, b) => {
          if (sortKey === "course_num") {
            const comparison = a.course_num.localeCompare(b.course_num, undefined, {
              numeric: true,
              sensitivity: "base",
            });
            return sortDirection === "asc" ? comparison : -comparison;
          }

          let aValue = a[sortKey];
          let bValue = b[sortKey];

          if (sortKey === "recommend") {
            aValue = a.metrics.recommend ?? -1;
            bValue = b.metrics.recommend ?? -1;
          } else if (sortKey === "challenge_rate") {
            aValue = a.metrics.challenge_rate ?? -1;
            bValue = b.metrics.challenge_rate ?? -1;
          }

          if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
          if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
          return 0;
        })
    : [];

  return (
    <div className="flex-1 overflow-y-auto bg-dark-gray p-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">

        {/* Page header */}
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
            onChange={(event) => setInputValue(event.target.value.toUpperCase())}
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
            Search for a department to see summary metrics, featured course views, and a
            sortable course explorer.
          </div>
        )}

        {deptData && (
          <>
            {/* Dept header + summary cards */}
            <div className="rounded-xl border border-[#4a1020] bg-gradient-to-br from-[#1e0a10] via-[#17080e] to-[#10050a] p-5">
              <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="text-sm uppercase tracking-wide text-[#a06070]">
                    {deptData.dept.campus}
                  </p>
                  <h3 className="text-2xl font-bold text-white">
                    {deptData.dept.name}{" "}
                    <span className="text-gold">({deptData.dept.code})</span>
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

            {/* Featured lists */}
            <div className="grid gap-4 xl:grid-cols-3">
              <FeaturedList
                title="Popular Courses"
                subtitle="Highest total enrollment in the department."
                items={deptData.featured.popular}
                metricLabel="Students"
                renderMetric={(course) => formatNumber(course.total_students)}
              />
              <FeaturedList
                title="Best Rated"
                subtitle="Highest recommend scores with at least 50 responses."
                items={deptData.featured.best_rated}
                metricLabel="Recommend"
                renderMetric={(course) => formatMetric(course.metrics.recommend)}
              />
              <FeaturedList
                title="Most Challenging"
                subtitle="Largest share of C-/D/F/W/N outcomes with at least 100 outcomes."
                items={deptData.featured.most_challenging}
                metricLabel="Challenge"
                renderMetric={(course) => formatPercent(course.metrics.challenge_rate)}
              />
            </div>

            {/* Course table */}
            <div className="rounded-xl border border-[#4a1020] bg-[#1e0a10] p-5">
              <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white">Course Explorer</h3>
                  <p className="text-sm text-[#a06070]">
                    Filter and sort the full department catalog without making another request.
                  </p>
                </div>

                <div className="flex flex-col gap-3 md:flex-row">
                  <input
                    type="text"
                    value={filterText}
                    onChange={(event) => setFilterText(event.target.value)}
                    placeholder="Filter by number or title"
                    className="rounded-lg border border-[#4a1020] bg-[#150709] p-2.5 text-white placeholder-[#7a3040] outline-none focus:border-gold/50"
                  />
                  <select
                    value={sortKey}
                    onChange={(event) => setSortKey(event.target.value)}
                    className="rounded-lg border border-[#4a1020] bg-[#150709] p-2.5 text-white outline-none"
                  >
                    <option value="total_students">Students</option>
                    <option value="course_num">Course Number</option>
                    <option value="recommend">Recommend</option>
                    <option value="challenge_rate">Challenge Rate</option>
                  </select>
                  <select
                    value={sortDirection}
                    onChange={(event) => setSortDirection(event.target.value)}
                    className="rounded-lg border border-[#4a1020] bg-[#150709] p-2.5 text-white outline-none"
                  >
                    <option value="desc">Descending</option>
                    <option value="asc">Ascending</option>
                  </select>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
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
                  <tbody>
                    {displayedCourses.map((course) => (
                      <tr key={course.id} className="border-b border-[#2a0d15] align-top hover:bg-[#1a0810] transition-colors">
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
                    ))}
                  </tbody>
                </table>
              </div>

              {displayedCourses.length === 0 && (
                <p className="mt-4 text-sm text-[#a06070]">
                  No courses matched your current filter.
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DepartmentExplorer;
