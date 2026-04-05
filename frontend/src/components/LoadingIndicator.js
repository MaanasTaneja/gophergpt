import React from "react";
import { GoldyMascot } from "./GoldyMascot";

export const LoadingIndicator = ({ label = "Thinking" }) => (
    <div className="flex items-start gap-3 mb-6">
        <GoldyMascot className="w-8 h-8 flex-shrink-0 mt-0.5" />
        <div className="flex items-center gap-2 pt-1">
            <span className="text-sm text-gray-400">{label}</span>
            <div className="flex gap-1">
                <div className="w-1.5 h-1.5 bg-gold rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-1.5 h-1.5 bg-gold rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-1.5 h-1.5 bg-gold rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
        </div>
    </div>
);
