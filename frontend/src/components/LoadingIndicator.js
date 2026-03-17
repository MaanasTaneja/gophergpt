import React from "react";
import { GoldyMascot } from "./GoldyMascot";

export const LoadingIndicator = ({ label = "Thinking..." }) => (
    <div className="flex justify-start mb-4">
        <div className="flex items-end">
        <GoldyMascot className="w-8 h-8 flex-shrink-0 mr-3" />
        <div className="gradient-border-message">
            <div className="px-3 py-2 text-gray-100">
            <div className="flex items-center space-x-2">
                <span className="text-sm">{label}</span>
                <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" />
                <div
                    className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                />
                <div
                    className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                />
                </div>
            </div>
            </div>
        </div>
        </div>
    </div>
);