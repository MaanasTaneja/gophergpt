import React, { useState, useRef, useEffect } from "react";
import "./App.css";
import { getLoadingLabel } from "./utils/loadingLabel";
import ChatPage from "./pages/ChatPage";
import Sidebar from "./components/Sidebar";
import DepartmentExplorer from "./pages/DepartmentExplorer";

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
  const isLoadedConversation = useRef(false); // prevent duplication of pages
  const conversationId = useRef(Date.now()); // stable id for current conversation, prevent duplications?

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
    // Skip animation for empty text or very long responses
    if (!text || text.length > 600) {
      if (text) setTypingMessage(text);
      setIsTyping(false);
      if (callback) callback();
      return;
    }

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
        // Type 3 characters at a time for snappier feel
        index = Math.min(index + 3, text.length);
        setTypingMessage(text.slice(0, index));
      } else {
        clearInterval(typeInterval);
        setIsTyping(false);
        if (callback) callback();
      }
    }, 12);
  };

  const doSend = async (userMessage) => {
    if (!userMessage.trim() || isLoading || isTyping) return;

    userScrolledUp.current = false;
    isLoadedConversation.current = false;

    setLoadingLabel(getLoadingLabel(userMessage));
    setIsLoading(true);
    setInputValue("");
    setMessages((prev) => [...prev, { text: userMessage, isUser: true, content: [] }]);
    setError(null);

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 90000); // 90s timeout

      const response = await fetch(`${process.env.REACT_APP_API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: conversationId.current,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      const botContent = Array.isArray(data.content) ? data.content : [];

      setIsLoading(false);
      typeMessage(data.response, () => {
        setMessages((prev) => {
          const updated = [...prev, { text: data.response, isUser: false, content: botContent }];
          setTimeout(() => saveConversation(updated), 0);
          return updated;
        });
        setTypingMessage("");
      });
    } catch (err) {
      console.error("Error sending message:", err);
      setIsLoading(false);
      const errText = err.name === "AbortError"
        ? "The request timed out. The agent may be overloaded — please try again."
        : "Sorry, I encountered an error. Please try again.";
      setError(errText);
      setMessages((prev) => [...prev, { text: errText, isUser: false, content: [] }]);
    }
  };

  const sendMessage = () => doSend(inputValue.trim());
  const sendDirect = (text) => doSend(text);

  // History Implementations

  // when app loads, fetch all saved conversations
  useEffect(() => {
    fetch(`${process.env.REACT_APP_API_BASE}/history`)
      .then(res => res.json())
      .then(data => {
        setConversations(data.conversations);
      });
  }, []);

  // saves current conversation into database, can be accessed again by button from history list
  const saveConversation = async (latestMessages) => {
    // prevent duplication of loaded conversations
    if (isLoadedConversation.current) return;

    // use passed messages (avoids stale closure), fall back to state
    const msgs = latestMessages || messages;

    // don't save empty or single message conversations
    if (msgs.length < 2) return;

    // create data structure using stable conversationId
    const conversation = {
      id: conversationId.current,
      title: msgs[0].text.slice(0, 40),
      messages: msgs
    };

    // sends conversation into storage
    const response = await fetch(`${process.env.REACT_APP_API_BASE}/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: conversation.id,
        title: conversation.title,
        messages: msgs
      })
    });

    // re-fetch from backend to stay in sync
    const data = await response.json();
    if (data.ok) {
      fetch(`${process.env.REACT_APP_API_BASE}/history`)
        .then(res => res.json())
        .then(data => {
          setConversations(data.conversations);
        });
    }
  };

  // saves current conversation to history, then starts a fresh chat
  const handleNewChat = async () => {
    isLoadedConversation.current = false;
    await saveConversation(); // stores full conversation before wiping
    conversationId.current = Date.now(); // generate new id for next conversation
    setMessages([]);
    setInputValue("");
    setError(null);
    userScrolledUp.current = false; // reset scroll lock on new chat
  };

  // loads the previous conversation
  const loadPrevChat = async (conversation) => {
    await saveConversation(); // stores current conversation before loading prev
    conversationId.current = conversation.id; // use loaded conversation's id
    setMessages(conversation.messages);
    setInputValue("");
    setCurrentPage("chat");
    isLoadedConversation.current = true; // prevent duplication of pages
    userScrolledUp.current = false; // reset scroll
  };

  const clearHistory = async () => {
    await fetch(`${process.env.REACT_APP_API_BASE}/history/clear`, { method: "DELETE" });
    setConversations([]);
  };

  // End of History

  return (
    <div className="flex h-screen overflow-hidden bg-dark-gray text-white">
      <Sidebar
        onNewChat={handleNewChat}
        onNavigate={setCurrentPage}
        currentPage={currentPage}
        conversations={conversations}
        onLoad={loadPrevChat}
        onClearHistory={clearHistory}
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
            onSendDirect={sendDirect}
          />
        )}
        {currentPage === "department" && <DepartmentExplorer />}
      </div>
    </div>
  );
}

export default App;
