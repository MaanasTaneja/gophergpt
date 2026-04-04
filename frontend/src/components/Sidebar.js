import React from "react";
import { History } from "./History";
import MinnesotaMLogo from "./MinnesotaMLogo";

const Sidebar = ({ onNewChat, onNavigate, conversations, onLoad }) => (
    <div className="w-64 h-screen sticky top-0 bg-dark-gray border-r border-gray-700 flex flex-col p-3">

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


        {/* History Section */}
        <div className="flex-1 overflow-y-auto min-h-0">
            <p className="text-gray-500 text-xs uppercase tracking-wider mb-2 px-2">History</p>
            <History conversations={conversations} onLoad={onLoad} />
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
