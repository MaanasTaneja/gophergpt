import React from "react";
import MinnesotaMLogo from "./MinnesotaMLogo";

const Sidebar = ({ onNewChat, onNavigate, currentPage }) => (
    <div className="w-64 h-screen sticky top-0 bg-dark-gray border-r border-gray-700 flex flex-col p-3 overflow-y-auto">

        {/* Logo */}
        <div className="flex items-center justify-center mb-4">
        <MinnesotaMLogo size="w-12 h-12" />
        </div>

        {/* New Chat Button */}
        <button
        onClick={() => {
            onNewChat();
            onNavigate("chat");
        }}
        className="w-full py-2 px-4 mb-6 text-left text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
        New Chat
        </button>

        {/* Apps Section */}
        <div className="mb-6">
        <p className="text-gray-500 text-xs uppercase tracking-wider mb-2 px-2">Apps</p>

        {/* Research - active */}
        <button
            onClick={() => onNavigate("research")}
            className={`w-full py-2 px-4 mb-1 text-left rounded-lg transition-colors ${
            currentPage === "research"
                ? "bg-gray-700 text-white"
                : "text-gray-400 hover:bg-gray-700"
            }`}
        >
            Research
        </button>

        {/* Placeholder tools - not yet ready */}
        <button disabled className="w-full py-2 px-4 mb-1 text-left text-gray-400 rounded-lg cursor-not-allowed">
            Tool 2
        </button>
        <button disabled className="w-full py-2 px-4 mb-1 text-left text-gray-400 rounded-lg cursor-not-allowed">
            Tool 3
        </button>
        </div>

        {/* History Section */}
        <div className="mb-6">
        <p className="text-gray-500 text-xs uppercase tracking-wider mb-2 px-2">History</p>
        <button disabled className="w-full py-2 px-4 text-left text-gray-400 rounded-lg cursor-not-allowed">
            Coming Soon
        </button>
        </div>

        {/* Settings - pinned to bottom */}
        <div className="mt-auto">
        <button disabled className="w-full py-2 px-4 text-left text-gray-400 rounded-lg cursor-not-allowed">
            Settings
        </button>
        </div>

    </div>
);

export default Sidebar;