import React from "react";
import { Message } from "./Message";
import { LoadingIndicator } from "./LoadingIndicator";

const ChatWindow = ({ messages, isTyping, typingMessage, isLoading, loadingLabel, error, messagesEndRef }) => (
    <div className="flex-1 overflow-y-auto relative z-10">
        <div className="max-w-3xl mx-auto px-4 pt-6 pb-8">
            {messages.map((message, index) => (
                <Message
                    key={index}
                    message={message.text}
                    isUser={message.isUser}
                    content={message.content}
                />
            ))}
            {isTyping && typingMessage && (
                <Message message={typingMessage} isUser={false} content={[]} />
            )}
            {isLoading && <LoadingIndicator label={loadingLabel} />}
            {error && (
                <div className="text-red-400 text-center text-sm py-2">{error}</div>
            )}
            <div ref={messagesEndRef} />
        </div>
    </div>
);

export default ChatWindow;
