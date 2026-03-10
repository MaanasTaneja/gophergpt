import React, { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import "./App.css";
import Research from "./Research"; // might scrap
import { getLoadingLabel } from "./utils/loadingLabel";
import { escapeHtml, linkify, boldify, formatBotMessage } from "./utils/messageFormatter";
import { Message } from "./components/Message";
import { LoadingIndicator } from "./components/LoadingIndicator";
import { MinnesotaMLogo } from "./components/MinnesotaMLogo";
import { GoldyMascot } from "./components/GoldyMascot";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import ChatPage from "./pages/ChatPage";

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
    <div className="flex min-h-screen bg-dark-gray text-white">
      <ChatPage
        messages={messages}
        isTyping={isTyping}
        typingMessage={typingMessage}
        isLoading={isLoading}
        loadingLabel={loadingLabel}
        error={error}
        messagesEndRef={messagesEndRef}
        inputValue={inputValue}
        setInputValue={setInputValue}
        onSend={sendMessage}
      />
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