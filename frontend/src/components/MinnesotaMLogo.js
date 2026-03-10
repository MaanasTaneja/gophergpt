import React from "react";

// Minnesota M Logo Component
export const MinnesotaMLogo = ({ size = "w-16 h-16", className = "" }) => (
    <div
        className={`${size} bg-white rounded-full flex items-center justify-center overflow-hidden ${className}`}
    >
        <img
        src="/minnesota-m-logo.png"
        alt="Minnesota M Logo"
        className="w-full h-full object-contain"
        onError={(e) => {
            // Fallback to text M if image fails to load
            e.target.style.display = "none";
            e.target.nextSibling.style.display = "block";
        }}
        />
        <span className="text-maroon font-bold text-2xl hidden">M</span>
    </div>
);