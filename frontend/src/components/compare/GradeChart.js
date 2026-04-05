import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer } from "recharts";

const GRADE_ORDER = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"];

// Color each bar: A/A-/B+ = gold, B/B- = gold-muted, C range = maroon-light, D/F = maroon
const gradeColor = (grade) => {
    if (["A", "A-", "B+"].includes(grade)) return "#FFCC33";
    if (["B", "B-"].includes(grade)) return "#e6b800";
    if (["C+", "C"].includes(grade)) return "#c44a2a";
    if (["C-", "D+"].includes(grade)) return "#a83020";
    return "#7A0019";
};

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="rounded-lg border border-[#4a1020] bg-[#1e0a10] px-3 py-2 text-sm shadow-xl">
            <p className="font-bold text-gold">{label}</p>
            <p className="text-white">{payload[0].value.toLocaleString()} students</p>
        </div>
    );
};

const GradeChart = ({ grades }) => {
    if (!grades) return null;

    const chartData = GRADE_ORDER
        .filter(grade => grades[grade] !== undefined)
        .map(grade => ({ grade, count: grades[grade] }));

    return (
        <div>
            <h3 className="text-white text-lg font-bold mb-4">Grade Distribution</h3>

            <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
                    <XAxis dataKey="grade" stroke="#FFCC33" tick={{ fill: "#FFCC33", fontSize: 12 }} />
                    <YAxis stroke="#4a1020" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(122,0,25,0.15)" }} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {chartData.map((entry) => (
                            <Cell key={entry.grade} fill={gradeColor(entry.grade)} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>

            <div className="flex gap-6 mt-4 text-sm text-gray-400 border-t border-[#4a1020] pt-3">
                <span>Withdrawn (W): <strong className="text-gold">{grades["W"] ?? 0}</strong></span>
                <span>Satisfactory (S): <strong className="text-gold">{grades["S"] ?? 0}</strong></span>
                <span>No Credit (N): <strong className="text-gold">{grades["N"] ?? 0}</strong></span>
            </div>
        </div>
    );
};

export default GradeChart;
