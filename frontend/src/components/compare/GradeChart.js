import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const GRADE_ORDER = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"];

const GradeChart = ({ grades }) => {

    if (!grades) {
        return null;
    }

    // transform grades object into sorted array for recharts
    const chartData = GRADE_ORDER
        .filter(grade => grades[grade] !== undefined)
        .map(grade => ({
            grade,
            count: grades[grade]
        }));

    return (
    <div>
        {/* Title */}
        <h3 className="text-white text-lg font-bold mb-4">Grade Distribution</h3>

        {/* Chart */}
        <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
                <XAxis dataKey="grade" stroke="#F0F0F0" />
                <YAxis stroke="#F0F0F0" />
                <Tooltip />
                <Bar dataKey="count" fill="#FFCC33" radius={[4, 4, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>

        {/* W, S, N stats */}
        <div className="flex gap-6 mt-4 text-sm text-gray-400">
            <span>Withdrawn (W): <strong className="text-white">{grades["W"] ?? 0}</strong></span>
            <span>Satisfactory (S): <strong className="text-white">{grades["S"] ?? 0}</strong></span>
            <span>No Credit (N): <strong className="text-white">{grades["N"] ?? 0}</strong></span>
        </div>

    </div>
    );
};

export default GradeChart;