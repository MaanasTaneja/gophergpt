import React, { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import "./App.css";
import Research from "./Research"; // might scrap
import { getLoadingLabel } from "./utils/loadingLabel";
import { escapeHtml, linkify, boldify, formatBotMessage } from "./utils/messageFormatter";
import { Message } from "./components/Message";
import { LoadingIndicator } from "./components/LoadingIndicator";

// Minnesota M Logo Component
const MinnesotaMLogo = ({ size = "w-16 h-16", className = "" }) => (
  <div
    className={`${size} bg-white rounded-full flex items-center justify-center overflow-hidden ${className}`}
  >
    <img
      src="/minnesota-m-logo.png"
      alt="Minnesota M Logo"
      className="w-full h-full object-contain"
      onError={(e) => {
        // Fallback to text M if image fails to load
        e.target.style.display = "none";
        e.target.nextSibling.style.display = "block";
      }}
    />
    <span className="text-maroon font-bold text-2xl hidden">M</span>
  </div>
);

// Goldy Gopher Mascot - Using your local image
const GoldyMascot = ({ className = "" }) => (
  <div className={`w-80 h-80 flex items-center justify-center ${className}`}>
    <img
      src="/goldy-gopher.png"
      alt="Goldy Gopher"
      className="w-full h-full object-contain"
      onError={(e) => {
        // Fallback to emoji if image fails to load
        e.target.style.display = "none";
        e.target.nextSibling.style.display = "block";
      }}
    />
    <div className="w-full h-full bg-gold rounded-full flex items-center justify-center hidden">
      <span className="text-maroon font-bold text-6xl">🐿️</span>
    </div>
  </div>
);

// Input Component
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
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={handleKeyPress}
          onFocus={onFocus}
          placeholder={placeholder}
          disabled={disabled}
          className="gradient-border-input flex-1 pr-12"
        />
        <button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="absolute right-2 w-8 h-8 bg-gold rounded-full flex items-center justify-center hover:bg-yellow-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed send-button"
        >
          <Send size={16} className="text-maroon" />
        </button>
      </div>
    </div>
  );
};

function App() {
  const [currentPage, setCurrentPage] = useState("landing"); // 'landing', 'transition', 'chat'
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showWelcome, setShowWelcome] = useState(true);
  const [typingMessage, setTypingMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const messagesEndRef = useRef(null);

  // Thinking Feature
  const [loadingLabel, setLoadingLabel] = useState("Thinking");

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, typingMessage]);

  // Typing animation function
  const typeMessage = (text, callback) => {
    setIsTyping(true);
    setTypingMessage("");
    let index = 0;

    const typeInterval = setInterval(() => {
      if (index < text.length) {
        setTypingMessage(text.slice(0, index + 1));
        index++;
      } else {
        clearInterval(typeInterval);
        setIsTyping(false);
        if (callback) callback();
      }
    }, 15); // 30ms delay between characters (like ChatGPT)
  };

  const handleInputFocus = () => {
    if (currentPage === "landing") {
      // Start transition
      setIsTransitioning(true);
      // Fade out welcome content first
      setShowWelcome(false);
      // Then transition to transition page after fade completes
      setTimeout(() => {
        setCurrentPage("transition");
        setIsTransitioning(false);
      }, 700); // Match the CSS transition duration
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading || isTyping) return;

    const userMessage = inputValue.trim();
    console.log("Sending message:", userMessage);

    // thinking feature
    setLoadingLabel(getLoadingLabel(userMessage));

    // if we want to add more features in-between the thinking, such as processing data, filtering, or whatever, do here:

    setIsLoading(true);
    setInputValue("");
    setMessages((prev) => [...prev, { text: userMessage, isUser: true }]);
    setError(null);

    // Don't transition to chat page - stay on transition page and show messages
    if (currentPage === "transition") {
      console.log("Staying on transition page, showing messages");
      // Keep currentPage as 'transition'
    }

    try {
      console.log("Making API request to backend...");
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage }),
      });

      console.log("Response status:", response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Response data:", data);

      // Wait 1 second before starting typing animation
      setTimeout(() => {

        setIsLoading(false);

        typeMessage(data.response, () => {
          // When typing is complete, add the full message to messages array
          setMessages((prev) => [
            ...prev,
            { text: data.response, isUser: false },
          ]);
          setTypingMessage("");
        });
      }, 1000);
    } catch (err) {
      console.error("Error sending message:", err);

      setIsLoading(false);

      setError("Sorry, I encountered an error. Please try again.");
      setMessages((prev) => [
        ...prev,
        {
          text: "Sorry, I encountered an error. Please try again.",
          isUser: false,
        },
      ]);
    } /* finally {
            setIsLoading(false);
        } */
  };

  return (
    <div className="min-h-screen bg-dark-gray text-white">
      {/* Simple top nav */}
      <div className="p-3 border-b border-gray-800 flex justify-end space-x-2">
        <button
          onClick={() => setCurrentPage("landing")}
          className={`px-3 py-1 rounded ${currentPage !== "research" ? "bg-gold text-maroon" : "bg-gray-800"}`}
        >
          Main
        </button>
        <button
          onClick={() => setCurrentPage("research")}
          className={`px-3 py-1 rounded ${currentPage === "research" ? "bg-gold text-maroon" : "bg-gray-800"}`}
        >
          Research
        </button>
      </div>
      {/* Landing Page */}
      {currentPage === "landing" && (
        <div className="min-h-screen flex flex-col px-4 page-transition">
          {/* Content Area */}
          <div className="flex-1 flex flex-col items-center justify-center">
            {/* Minnesota M Logo */}
            <MinnesotaMLogo
              className={`mb-8 fade-in-up transition-opacity duration-700 ${showWelcome ? "opacity-100" : "opacity-0"}`}
            />

            {/* Welcome Text */}
            <div
              className={`text-center mb-12 fade-in-up transition-opacity duration-700 ${showWelcome ? "opacity-100" : "opacity-0"}`}
            >
              <h1 className="text-5xl font-bold text-gold mb-4">
                Hey Gophers! Welcome To GopherGPT
              </h1>
              <p className="text-2xl text-gold">How Can We Help You?</p>
            </div>

            {/* Goldy Mascot */}
            <div
              className={`mb-12 fade-in-up transition-opacity duration-700 ${showWelcome ? "opacity-100" : "opacity-0"}`}
            >
              <GoldyMascot />
            </div>
          </div>

          {/* Input Box - Expands during transition */}
          <div
            className={`w-full mx-auto pb-4 fade-in-up transition-all duration-700 ${isTransitioning ? "px-4" : "max-w-2xl"}`}
          >
            <ChatInput
              value={inputValue}
              onChange={setInputValue}
              onSend={sendMessage}
              onFocus={handleInputFocus}
              placeholder="Ask GopherGPT anything....."
            />
          </div>
        </div>
      )}

      {/* Research Page */}
      {currentPage === "research" && <Research />}

      {/* Transition Page */}
      {currentPage === "transition" && (
        <div className="min-h-screen flex flex-col px-4 page-transition">
          {/* Header with Logo */}
          <div className="p-4 border-b border-gray-700">
            <MinnesotaMLogo size="w-12 h-12" />
          </div>

          {/* Large Faded M Logo - NO CIRCLE */}
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
            <span className="text-maroon font-bold text-9xl opacity-10 hidden">
              M
            </span>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 relative z-10">
            {messages.map((message, index) => (
              <Message
                key={index}
                message={message.text}
                isUser={message.isUser}
              />
            ))}
            {isTyping && typingMessage && (
              <Message message={typingMessage} isUser={false} />
            )}
            {isLoading && <LoadingIndicator label={loadingLabel} />}
            {error && (
              <div className="text-red-400 text-center text-sm">{error}</div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Box - Smoothly expands to full width */}
          <div className="w-full px-4 pb-4 transition-all duration-700">
            <ChatInput
              value={inputValue}
              onChange={setInputValue}
              onSend={sendMessage}
              placeholder="Ask GopherGPT anything....."
              disabled={isLoading || isTyping}
            />
          </div>
        </div>
      )}

      {/* Chat Interface */}
      {currentPage === "chat" && (
        <div className="min-h-screen flex flex-col page-transition">
          {/* Header with Logo */}
          <div className="p-4 border-b border-gray-700">
            <MinnesotaMLogo size="w-12 h-12" />
          </div>

          {/* Faded Background M Logo */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-96 h-96 bg-white rounded-full flex items-center justify-center opacity-5 overflow-hidden">
              <img
                src="/minnesota-m-logo.png"
                alt="Minnesota M Logo"
                className="w-full h-full object-contain"
                onError={(e) => {
                  e.target.style.display = "none";
                  e.target.nextSibling.style.display = "block";
                }}
              />
              <span className="text-maroon font-bold text-9xl hidden">M</span>
            </div>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 relative z-10">
            {messages.map((message, index) => (
              <Message
                key={index}
                message={message.text}
                isUser={message.isUser}
              />
            ))}
            {isLoading && <LoadingIndicator label={loadingLabel} />}
            {error && (
              <div className="text-red-400 text-center text-sm">{error}</div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <div className="p-4 border-t border-gray-700 relative z-10">
            <ChatInput
              value={inputValue}
              onChange={setInputValue}
              onSend={sendMessage}
              placeholder="Ask GopherGPT anything....."
              disabled={isLoading || isTyping}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;



/*

Note:

This file once refactored should only render in the sidebar and whatever page is currently active

Goal:
- Only actively render Sidebar, and their components, and whatever page is actively being rendered, all functions should be compartmentalized into their respective files.


*/