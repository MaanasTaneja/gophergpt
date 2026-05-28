import React, { useState } from "react";
import { History } from "./History";
import MinnesotaMLogo from "./MinnesotaMLogo";

const Sidebar = ({ onNewChat, onNavigate, currentPage, conversations, onLoad, onClearHistory }) => {
    const [confirming, setConfirming] = useState(false);

    const handleClear = () => {
        if (confirming) {
            onClearHistory();
            setConfirming(false);
        } else {
            setConfirming(true);
            setTimeout(() => setConfirming(false), 3000);
        }
    };

    return (
        <div className="w-64 h-screen sticky top-0 bg-dark-gray border-r border-gray-700 flex flex-col p-3">

            {/* Logo */}
            <div className="flex items-center justify-center mb-4">
                <MinnesotaMLogo size="w-12 h-12" />
            </div>

            {/* New Chat Button */}
            <button
                onClick={() => { onNewChat(); onNavigate("chat"); }}
                className="w-full py-2 px-4 mb-6 text-left text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
                New Chat
            </button>

            {/* Apps Section */}
            <div className="mb-6">
                <p className="text-gray-500 text-xs uppercase tracking-wider mb-2 px-2">Apps</p>
                <button
                    onClick={() => onNavigate("department")}
                    className={`w-full py-2 px-4 mb-1 text-left rounded-lg transition-colors ${
                        currentPage === "department"
                            ? "bg-gray-700 text-white"
                            : "text-gray-400 hover:bg-gray-700"
                    }`}
                >
                    Department Explorer
                </button>
            </div>

            {/* History Section */}
            <div className="flex-1 overflow-y-auto min-h-0">
                <div className="flex items-center justify-between mb-2 px-2">
                    <p className="text-gray-500 text-xs uppercase tracking-wider">History</p>
                    {conversations && conversations.length > 0 && (
                        <button
                            onClick={handleClear}
                            className={`text-xs transition-colors ${
                                confirming
                                    ? "text-red-400 font-semibold"
                                    : "text-gray-600 hover:text-gray-400"
                            }`}
                        >
                            {confirming ? "Confirm?" : "Clear"}
                        </button>
                    )}
                </div>
                <History conversations={conversations} onLoad={onLoad} />
            </div>

            {/* Profile Button — pinned to bottom */}
            <div className="border-t border-gray-700 pt-3 mt-2">
                <button
                    onClick={() => onNavigate("profile")}
                    className={`w-full py-2 px-4 text-left rounded-lg transition-colors flex items-center gap-2 ${
                        currentPage === "profile"
                            ? "bg-gray-700 text-white"
                            : "text-gray-400 hover:bg-gray-700"
                    }`}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="8" r="4" />
                        <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
                    </svg>
                    Profile
                </button>
            </div>

        </div>
    );
};

export default Sidebar;
