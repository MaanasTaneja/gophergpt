import React from "react";

export const GoldyMascot = ({ className = "w-80 h-80" }) => (
    <div className={`flex items-center justify-center ${className}`}>
        <img
        src="/goldy-gopher.png"
        alt="Goldy Gopher"
        className="w-full h-full object-contain"
        onError={(e) => {
            e.target.style.display = "none";
            e.target.nextSibling.style.display = "block";
        }}
        />
        <div className="w-full h-full bg-gold rounded-full flex items-center justify-center hidden">
        <span className="text-maroon font-bold text-6xl">🐿️</span>
        </div>
    </div>
);