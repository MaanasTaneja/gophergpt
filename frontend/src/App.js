import React, { useState, useRef, useEffect } from "react";
import "./App.css";
import { getLoadingLabel } from "./utils/loadingLabel";
import ChatPage from "./pages/ChatPage";
import Sidebar from "./components/Sidebar";
import Research from "./pages/Research";

function App() {
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [typingMessage, setTypingMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [loadingLabel, setLoadingLabel] = useState("Thinking");
  const [currentPage, setCurrentPage] = useState("chat");
  const [conversations, setConversations] = useState([]);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const userScrolledUp = useRef(false);

  const isNearBottom = () => {
    const container = chatContainerRef.current;
    if (!container) return true;
    const threshold = 50;
    return container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
  };

  const scrollToBottom = () => {
    if (!userScrolledUp.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, typingMessage]);

  // Listen for manual scrolling
  useEffect(() => {
    const container = chatContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      userScrolledUp.current = !isNearBottom();
    };

    container.addEventListener("scroll", handleScroll);
    return () => container.removeEventListener("scroll", handleScroll);
  }, [currentPage]);

  const typeMessage = (text, callback) => {
    setIsTyping(true);
    setTypingMessage("");
    let index = 0;

    const typeInterval = setInterval(() => {
      // If tab is hidden, complete instantly to avoid browser throttling
      if (document.hidden) {
        clearInterval(typeInterval);
        setTypingMessage(text);
        setIsTyping(false);
        if (callback) callback();
        return;
      }

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

    userScrolledUp.current = false; // reset scroll lock on new message

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

  // saves current conversation into database, can be accessed again by button from history list
  const saveConversation = () => {

    // checks if the page is empty, shouldn't save empty conversation into history
    if (messages.length === 0) {
      return;
    };

    // create data structure for conversation
    const conversation = {
      id: Date.now(), // unique id
      title: messages[0].text.slice(0, 30), // store 30char length of first prompt as title
      messages: messages // store full conversation
    };


    setConversations(prev => [conversation, ...prev]);
  };


  // saves current conversation to history, then starts a fresh chat
  const handleNewChat = () => {
    saveConversation(); // stores full conversation before wiping
    setMessages([]);
    setInputValue("");
    setError(null);
    userScrolledUp.current = false; // reset scroll lock on new chat
  };

  return (
    <div className="flex h-screen overflow-hidden bg-dark-gray text-white">
      <Sidebar
        onNewChat={handleNewChat}
        onNavigate={setCurrentPage}
        currentPage={currentPage}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        {currentPage === "chat" && (
          <ChatPage
            messages={messages}
            isTyping={isTyping}
            typingMessage={typingMessage}
            isLoading={isLoading}
            loadingLabel={loadingLabel}
            error={error}
            messagesEndRef={messagesEndRef}
            chatContainerRef={chatContainerRef}
            inputValue={inputValue}
            setInputValue={setInputValue}
            onSend={sendMessage}
          />
        )}
        {currentPage === "research" && <Research />}
      </div>
    </div>
  );
}

export default App;