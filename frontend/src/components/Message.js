import React from "react";
import { formatBotMessage } from "../utils/messageFormatter";
import { GoldyMascot } from "./GoldyMascot";
import RichContent from "./RichContent";

export const Message = ({ message, isUser, content = [] }) => {
    if (isUser) {
        return (
            <div className="flex justify-end mb-5 message-bubble">
                <div className="flex items-end gap-2 max-w-[78%]">
                    <div className="gradient-border-message">
                        <div className="px-4 py-2.5 text-gray-100 text-sm leading-relaxed">
                            {message}
                        </div>
                    </div>
                    <div
                        className="w-7 h-7 rounded-full flex-shrink-0"
                        style={{ background: "linear-gradient(135deg, #3B82F6, #8B5CF6)" }}
                    />
                </div>
            </div>
        );
    }

    return (
        <div className="flex items-start gap-3 mb-6 message-bubble">
            <GoldyMascot className="w-8 h-8 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
                {message && (
                    <div
                        className={`bot-message${content.length ? " mb-3" : ""}`}
                        dangerouslySetInnerHTML={{ __html: formatBotMessage(message) }}
                    />
                )}
                {content.length > 0 && <RichContent content={content} />}
            </div>
        </div>
    );
};
