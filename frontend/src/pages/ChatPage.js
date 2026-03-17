import React from "react";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";

const ChatPage = ({
    messages,
    isTyping,
    typingMessage,
    isLoading,
    loadingLabel,
    error,
    messagesEndRef,
    chatContainerRef,
    inputValue,
    setInputValue,
    onSend,
    }) => (
    <div className="flex-1 flex flex-col h-screen relative">

        {/* Faded Background Logo */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <img
            src="/minnesota-m-logo.png"
            alt="Minnesota M Logo"
            className="w-[500px] h-[500px] object-contain opacity-10"
            onError={(e) => {
            e.target.style.display = "none";
            e.target.nextSibling.style.display = "block";
            }}
        />
        <span className="text-maroon font-bold text-9xl opacity-10 hidden">M</span>
        </div>

        {/* Messages - only this section scrolls */}
        <div ref={chatContainerRef} className="flex-1 overflow-y-auto relative z-10">
        <ChatWindow
            messages={messages}
            isTyping={isTyping}
            typingMessage={typingMessage}
            isLoading={isLoading}
            loadingLabel={loadingLabel}
            error={error}
            messagesEndRef={messagesEndRef}
        />
        </div>

        {/* Input - stays fixed at bottom */}
        <div className="p-4 border-t border-gray-700 relative z-10 bg-dark-gray">
        <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSend={onSend}
            placeholder="Ask GopherGPT anything....."
            disabled={isLoading || isTyping}
        />
        </div>

    </div>
);

export default ChatPage;