import React from "react";
import { formatBotMessage } from "../utils/messageFormatter";
import { GoldyMascot } from "./GoldyMascot";
import RichContent from "./RichContent";

export const Message = ({ message, isUser, content = [] }) => (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 message-bubble`}>
        <div className="flex items-end w-full">

        {/* User message */}
        {isUser ? (
            <>
            <div className="gradient-border-message ml-auto">
                <div className="px-3 py-2 text-gray-100">{message}</div>
            </div>
            <div
                className="w-8 h-8 rounded-full flex-shrink-0 ml-3"
                style={{ background: "linear-gradient(135deg, #3B82F6, #8B5CF6)" }}
            />
            </>
        ) : (

            /* Bot message */
            <>
            <GoldyMascot className="w-8 h-8 flex-shrink-0 mr-3" />
            <div className="gradient-border-message flex-1">
                <div className="px-3 py-2 text-gray-100">
                    <div dangerouslySetInnerHTML={{ __html: formatBotMessage(message) }} />
                    <RichContent content={content} />
                </div>
            </div>
            </>
        )}

        </div>
    </div>
);
