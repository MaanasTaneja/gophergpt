/* 
Note: This file should only contain the input bar, allowing the user to input their prompt.

Goal:
- Compartmentalize the input box into here
- This input box should be scrollable not swipe-able.
- Should always be rendered
*/

import React from "react";
import { Send } from "lucide-react";

const ChatInput = ({
    value,
    onChange,
    onSend,
    onFocus,
    placeholder,
    disabled = false,
    }) => {
    const handleKeyPress = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        onSend();
        }
    };

    return (
        <div className="gradient-border w-full max-w-2xl mx-auto relative">
        <div className="flex items-center">
            <textarea
            value={value}
            onChange={(e) => {
                onChange(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = e.target.scrollHeight + "px";
            }}
            onKeyPress={handleKeyPress}
            onFocus={onFocus}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="gradient-border-input flex-1 pr-12 resize-none overflow-y-auto"
            style={{ maxHeight: "200px" }}
            />
            <button
            onClick={onSend}
            disabled={disabled || !value.trim()}
            className="absolute right-2 bottom-2 w-8 h-8 bg-gold rounded-full flex items-center justify-center hover:bg-yellow-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed send-button"
            >
            <Send size={16} className="text-maroon" />
            </button>
        </div>
        </div>
    );
};

export default ChatInput;