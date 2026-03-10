import React from "react";

// Goldy Gopher Mascot - Using your local image
export const GoldyMascot = ({ className = "" }) => (
    <div className={`w-80 h-80 flex items-center justify-center ${className}`}>
        <img
        src="/goldy-gopher.png"
        alt="Goldy Gopher"
        className="w-full h-full object-contain"
        onError={(e) => {
            // Fallback to emoji if image fails to load
            e.target.style.display = "none";
            e.target.nextSibling.style.display = "block";
        }}
        />
        <div className="w-full h-full bg-gold rounded-full flex items-center justify-center hidden">
        <span className="text-maroon font-bold text-6xl">🐿️</span>
        </div>
    </div>
);