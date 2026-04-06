import React from "react";
import { Message } from "./Message";
import { LoadingIndicator } from "./LoadingIndicator";

const ChatWindow = ({ messages, isTyping, typingMessage, isLoading, loadingLabel, error, messagesEndRef}) => (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 relative z-10">
        {messages.map((message, index) => (<Message key={index} message={message.text} isUser={message.isUser} />))}
        {isTyping && typingMessage && (
            <Message message={typingMessage} isUser={false} isTyping={true} />
        )}
        {isLoading && <LoadingIndicator label={loadingLabel} />}
        {error && (<div className="text-red-400 text-center text-sm">{error}</div>)}
        <div ref={messagesEndRef} />
    </div>
);

export default ChatWindow;