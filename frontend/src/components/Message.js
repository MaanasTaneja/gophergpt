/* 
Note: This file should only contain the functions responsible for creating each message bubbles

Goal:
- This function should be called each time a input or output is provided, creating the bubbles of the conversation
*/

import React from "react"
import { formatBotMessage } from "../utils/messageFormatter";

// Message Component
export const Message = ({ message, isUser }) => (
    <div
        className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 message-bubble`}
    >
        <div className="flex items-end max-w-xs lg:max-w-md">
        {/* For user messages: Avatar on right, bubble on left */}
        {isUser ? (
            <>
            <div className="gradient-border-message">
                <div className="px-3 py-2 text-gray-800">{message}</div>
            </div>
            <div
                className="w-8 h-8 rounded-full flex-shrink-0 ml-3"
                style={{
                background: "linear-gradient(135deg, #3B82F6, #8B5CF6)", // Blue to purple gradient
                }}
            ></div>
            </>
        ) : (
            <>
            <div
                className="w-8 h-8 rounded-full flex-shrink-0 mr-3"
                style={{
                background: "linear-gradient(135deg, #F97316, #EF4444)", // Orange to red gradient
                }}
            ></div>
            <div className="gradient-border-message">
                <div
                className="px-3 py-2 text-gray-800"
                id="bot-message-html"
                dangerouslySetInnerHTML={{ __html: formatBotMessage(message) }}
                />
            </div>
            </>
        )}
        </div>
    </div>
);