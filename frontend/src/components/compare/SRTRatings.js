import React from "react";

const SRT_LABELS = {
    DEEP_UND: "Deep Understanding",
    STIM_INT: "Stimulating Interest",
    TECH_EFF: "Technical Effectiveness",
    ACC_SUP: "Accessible Support",
    EFFORT: "Effort Required",
    GRAD_STAND: "Grading Standards",
    RECC: "Would Recommend"
};

const SRTRatings = ({ srtVals }) => {

    if (!srtVals) {
        return null;
    }

    // parsing SRT vals from json into usable text
    const ratings = JSON.parse(srtVals);

    return (
        <div>
            {/* Title */}
            <h3 className="text-white text-lg font-bold mb-4">Course Ratings</h3>

            {/* Loop over SRT_LABELS and display each rating */}
            {Object.entries(SRT_LABELS).map(([key, label]) => (
                <div key={key} className="flex justify-between mb-2">
                    <span className="text-gray-400">{label}</span>
                    <span className="text-white font-bold">
                        {/* display the rating here, rounded to 2 decimal places */}
                        {ratings[key] ? ratings[key].toFixed(2) : "N/A"} / 6
                    </span>
                </div>
            ))}

        </div>
    );
};

export default SRTRatings;