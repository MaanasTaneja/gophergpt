/* 
Note: This file should only contain the functions responsible for creating the loading bubbles...

Goal:
- This function should be called each time a loading indicator is needed...
*/

import React from "react";

// Loading Indicator
export const LoadingIndicator = ({ label = "Thinking..." }) => (
    <div className="flex justify-start mb-4">
        <div className="flex items-end">
        <div
            className="w-8 h-8 rounded-full mr-3"
            style={{
            background: "linear-gradient(135deg, #F97316, #EF4444)", // Orange to red gradient
            }}
        ></div>
        <div className="gradient-border-message">
            <div className="px-3 py-2 text-gray-800">
            {/* Thinking Feature */}
            <div className="flex items-center space-x-2">
                <span className="text-sm">{label}</span>

                <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"></div>
                <div
                    className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                ></div>
                <div
                    className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                ></div>
                </div>
            </div>
            </div>
        </div>
        </div>
    </div>
);