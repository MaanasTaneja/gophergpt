import React from "react";
import CoursePanel from "../components/compare/CoursePanel";

const CourseCompare = () => (
    <div className="flex-1 flex h-full">

        {/* Left Panel */}
        <div className="flex-1 border-r border-gray-700 overflow-y-auto">
            <CoursePanel />
        </div>

        {/* Right Panel */}
        <div className="flex-1 overflow-y-auto">
            <CoursePanel />
        </div>

    </div>
);

export default CourseCompare;