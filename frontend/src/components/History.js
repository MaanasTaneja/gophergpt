import React from "react";

export const History = ({ conversations, onLoad }) => (
    <div>
    {conversations.map(conversation => (
        <button
        key={conversation.id}
        onClick={() => onLoad(conversation)}
        className="w-full py-2 px-4 mb-1 text-left rounded-lg transition-colors text-gray-400 hover:bg-gray-700"
        >
        {conversation.title}
        </button>
    ))}
    </div>
)