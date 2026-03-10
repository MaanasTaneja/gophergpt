import React, { useState, useRef, useEffect } from "react";
import "./App.css";
import { getLoadingLabel } from "./utils/loadingLabel";
import ChatPage from "./pages/ChatPage";
import Sidebar from "./components/Sidebar";

function App() {
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [typingMessage, setTypingMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [loadingLabel, setLoadingLabel] = useState("Thinking");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, typingMessage]);

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
    }, 15);
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading || isTyping) return;

    const userMessage = inputValue.trim();
    setLoadingLabel(getLoadingLabel(userMessage));
    setIsLoading(true);
    setInputValue("");
    setMessages((prev) => [...prev, { text: userMessage, isUser: true }]);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      setTimeout(() => {
        setIsLoading(false);
        typeMessage(data.response, () => {
          setMessages((prev) => [...prev, { text: data.response, isUser: false }]);
          setTypingMessage("");
        });
      }, 1000);
    } catch (err) {
      console.error("Error sending message:", err);
      setIsLoading(false);
      setError("Sorry, I encountered an error. Please try again.");
      setMessages((prev) => [
        ...prev,
        { text: "Sorry, I encountered an error. Please try again.", isUser: false },
      ]);
    }
  };

  // this isn't ready, just wipes chat logs, doesn't save, pending backend to support this feature...
  const handleNewChat = () => {
    setMessages([]);
    setInputValue("");
    setError(null);
  };

  return (
    <div className="flex min-h-screen bg-dark-gray text-white">
      <Sidebar onNewChat={handleNewChat} />
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