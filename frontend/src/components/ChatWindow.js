/* 
Note: This file should only contain the active chat interaction between agent and user, and nothing more.

Goal:
- Compartmentalize App.js, to include the response window and the interaction component.
- This should allow the menu to be scrollable, and not locked/bounded while the agent is responding

*/
import React from "react";
import { Message } from "./Message";
import { LoadingIndicator } from "./LoadingIndicator";

const ChatWindow = ({ messages, isTyping, typingMessage, isLoading, loadingLabel, error, messagesEndRef}) => (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 relative z-10">
        {messages.map((message, index) => (<Message key={index} message={message.text} isUser={message.isUser} />))}
        {isTyping && typingMessage && (<Message message={typingMessage} isUser={false} />)}
        {isLoading && <LoadingIndicator label={loadingLabel} />}
        {error && (<div className="text-red-400 text-center text-sm">{error}</div>)}
        <div ref={messagesEndRef} />
    </div>
);

export default ChatWindow;