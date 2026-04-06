import React from "react";

const SRT_LABELS = {
    DEEP_UND: "Deep Understanding",
    STIM_INT: "Stimulating Interest",
    TECH_EFF: "Technical Effectiveness",
    ACC_SUP: "Accessible Support",
    EFFORT: "Effort Required",
    GRAD_STAND: "Grading Standards",
    RECC: "Would Recommend",
};

// Interpolate from maroon (#7A0019) to gold (#FFCC33) based on 0–6 scale
const ratingColor = (value) => {
    if (value === null || value === undefined) return "#4a1020";
    const ratio = Math.min(value / 6, 1);
    // maroon → gold blend
    const r = Math.round(122 + (255 - 122) * ratio);
    const g = Math.round(0 + (204 - 0) * ratio);
    const b = Math.round(25 + (51 - 25) * ratio);
    return `rgb(${r},${g},${b})`;
};

const SRTRatings = ({ srtVals }) => {
    if (!srtVals) return null;

    const ratings = typeof srtVals === "string" ? JSON.parse(srtVals) : srtVals;

    return (
        <div>
            <h3 className="text-white text-lg font-bold mb-4">Course Ratings</h3>

            <div className="space-y-3">
                {Object.entries(SRT_LABELS).map(([key, label]) => {
                    const raw = ratings[key];
                    const value = raw !== null && raw !== undefined ? Number(raw) : null;
                    const pct = value !== null ? `${((value / 6) * 100).toFixed(1)}%` : "0%";
                    const color = ratingColor(value);

                    return (
                        <div key={key}>
                            <div className="flex justify-between mb-1 text-sm">
                                <span className="text-gray-300">{label}</span>
                                <span className="font-semibold" style={{ color }}>
                                    {value !== null ? `${value.toFixed(2)} / 6` : "N/A"}
                                </span>
                            </div>
                            <div className="h-2 w-full rounded-full bg-[#3a1020] overflow-hidden">
                                <div
                                    className="h-full rounded-full transition-all duration-500"
                                    style={{ width: pct, background: `linear-gradient(90deg, #7A0019, ${color})` }}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default SRTRatings;
