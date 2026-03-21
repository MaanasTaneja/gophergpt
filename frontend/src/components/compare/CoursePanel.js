import React, { useState } from "react";

import GradeChart from "./GradeChart"
import SRTRatings from "./SRTRatings"

const CoursePanel = () => {
    const [inputValue, setInputValue] = useState("");
    const [courseData, setCourseData] = useState(null);
    const [hasError, setHasError] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");

    const fetchCourse = async () => {
        if (!inputValue.trim()) return;

        try {
            const response = await fetch(`${process.env.REACT_APP_API_BASE}/umn/course`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: inputValue.trim() })
            });

            const data = await response.json();

            if (!data.ok || !data.search?.success) {
                setHasError(true);
                setErrorMessage("Cannot find course — check the course code and try again.");
                setCourseData(null);
                return;
            }

            // console.log("API Response:", data);
            setCourseData(data);

        } catch (err) {
            setHasError(true);
            setErrorMessage("Something went wrong. Please try again.");
            setCourseData(null);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === "Enter") {
            fetchCourse();
        }
    };

    return (
        <div className="flex-1 flex flex-col p-6">

            {/* Input box */}
            <input
                type="text"
                value={inputValue}
                onChange={(e) => {
                    setInputValue(e.target.value);
                    setHasError(false);
                    setErrorMessage("");
                }}
                onKeyPress={handleKeyPress}
                placeholder="Enter course code (e.g. CSCI 4041)"
                className={`w-full p-3 rounded-lg bg-gray-800 text-white border ${
                    hasError ? "border-red-500" : "border-gray-600"
                }`}
            />

            {/* Error message */}
            {hasError && (
                <p className="text-red-500 text-sm mt-1">{errorMessage}</p>
            )}

            {/* Data shows here when loaded */}
            {courseData && courseData["class"] && courseData["class"].data && (
                <div className="mt-6 flex flex-col gap-8">
                    <GradeChart grades={courseData["class"].data.total_grades} />
                    <SRTRatings srtVals={courseData["class"].data.srt_vals} />
                </div>
            )}
        </div>
    );

}; 

export default CoursePanel;