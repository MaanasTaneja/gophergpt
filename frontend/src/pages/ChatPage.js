import React from "react";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";

const SUGGESTIONS = [
  { label: "What is CSCI 4041 like?", sub: "Algorithms & Data Structures" },
  { label: "Compare CSCI 1933 and CSCI 1913", sub: "Side-by-side grade breakdown" },
  { label: "Who teaches MATH 1271?", sub: "Professors & ratings" },
  { label: "Research opportunities in computer science", sub: "UMN research programs" },
];

const WelcomeScreen = ({ onSend }) => (
  <div className="flex-1 flex flex-col items-center justify-center px-6 pb-8 relative z-10">
    <div className="mb-8 text-center">
      <h1 className="text-3xl font-semibold text-white mb-2">
        Welcome to <span className="text-gold">GopherGPT</span>
      </h1>
      <p className="text-gray-400 text-sm">
        Your AI guide to courses, professors, and research at the University of Minnesota.
      </p>
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
      {SUGGESTIONS.map((s) => (
        <button
          key={s.label}
          onClick={() => onSend(s.label)}
          className="text-left rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 hover:border-gold/40 hover:bg-white/[0.08] transition-all duration-150"
        >
          <p className="text-sm font-medium text-white">{s.label}</p>
          <p className="text-xs text-gray-400 mt-0.5">{s.sub}</p>
        </button>
      ))}
    </div>
  </div>
);

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
  onSendDirect,
}) => {
  const isEmpty = messages.length === 0 && !isLoading && !isTyping;

  return (
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

      {/* Messages or Welcome Screen */}
      <div ref={chatContainerRef} className="flex-1 overflow-y-auto relative z-10 flex flex-col">
        {isEmpty ? (
          <WelcomeScreen onSend={onSendDirect} />
        ) : (
          <ChatWindow
            messages={messages}
            isTyping={isTyping}
            typingMessage={typingMessage}
            isLoading={isLoading}
            loadingLabel={loadingLabel}
            error={error}
            messagesEndRef={messagesEndRef}
          />
        )}
      </div>

      {/* Input - stays fixed at bottom */}
      <div className="border-t border-gray-700 relative z-10 bg-dark-gray py-3 px-4">
        <div className="max-w-3xl mx-auto">
          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSend={onSend}
            placeholder="Ask GopherGPT anything..."
            disabled={isLoading || isTyping}
          />
        </div>
      </div>

    </div>
  );
};

export default ChatPage;
