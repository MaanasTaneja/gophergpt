/* 
Note: This file should only contain the sidebar and it's supports, such as a nav bar (if exist), history list (from History.js), and app links (possible app integration).


Goal:
- Create the sidebar, should maintain the left column, scrollable for additional histories.
- Integrate history rows, and possible nav bar (possible search button or bar to locate history or landing page).
- Everything should be a button for redirects.
- New Chat Button which reset active chat and stores into history

*/

import React from "react";
import MinnesotaMLogo from "./MinnesotaMLogo";


const Sidebar = ({ onNewChat }) => (
    <div className="w-64 min-h-screen bg-dark-gray border-r border-gray-700 flex flex-col p-3">

        {/* Logo */}
        <div className="flex items-center justify-center mb-4">
        <MinnesotaMLogo size="w-12 h-12" />
        </div>

        {/* New Chat Button */}
        <button
        onClick={onNewChat}
        className="w-full py-2 px-4 mb-6 bg-gold text-maroon font-bold rounded hover:bg-yellow-400 transition-colors"
        >
        + New Chat
        </button>

        {/* Apps Section */}
        <div className="mb-6">
        <p className="text-gray-500 text-xs uppercase tracking-wider mb-2 px-2">Apps</p>
        <button
            disabled
            className="w-full py-2 px-4 mb-6 bg-gold text-maroon font-bold rounded hover:bg-yellow-400 transition-colors"
        >
            🔧 Tool 1
        </button>
        <button
            disabled
            className="w-full py-2 px-4 mb-6 bg-gold text-maroon font-bold rounded hover:bg-yellow-400 transition-colors"
        >
            🔧 Tool 2
        </button>
        <button
            disabled
            className="w-full py-2 px-4 mb-6 bg-gold text-maroon font-bold rounded hover:bg-yellow-400 transition-colors"
        >
            🔧 Tool 3
        </button>
        </div>

        {/* History Section */}
        <div className="mb-6">
        <p className="text-gray-500 text-xs uppercase tracking-wider mb-2 px-2">History</p>
        <button
            disabled
            className="w-full py-2 px-4 mb-6 bg-gold text-maroon font-bold rounded hover:bg-yellow-400 transition-colors"
        >
            🕘 Coming Soon
        </button>
        </div>

        {/* Settings - pinned to bottom */}
        <div className="mt-auto">
        <button
            disabled
            className="w-full py-2 px-4 bg-gold text-maroon font-bold rounded hover:bg-yellow-400 transition-colors"
        >
            ⚙️ Settings
        </button>
        </div>

    </div>
);

export default Sidebar;