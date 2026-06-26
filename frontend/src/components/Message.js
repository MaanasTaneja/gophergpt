import React from "react";
import { formatBotMessage } from "../utils/messageFormatter";
import RichContent from "./RichContent";

const BotAvatar = () => (
  <div style={{
    width: 34, height: 34, borderRadius: "50%", flexShrink: 0,
    background: "#fff",
    boxShadow: "0 2px 10px rgba(0,0,0,.32)",
    display: "flex", alignItems: "center", justifyContent: "center",
    marginTop: 2,
  }}>
    <span style={{ color: "#7A0019", fontFamily: "Georgia, serif", fontSize: 16, fontWeight: 800, lineHeight: 1, userSelect: "none" }}>M</span>
  </div>
);

export const Message = ({ message, isUser, content = [] }) => {
  if (isUser) {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 20 }} className="message-bubble">
        <div style={{
          background: "rgba(122,0,25,.45)",
          border: "1px solid rgba(255,204,51,.15)",
          borderRadius: "16px 16px 4px 16px",
          padding: "12px 17px",
          maxWidth: "78%",
          color: "#f3eff0", fontSize: 14.5, lineHeight: 1.5,
        }}>
          {message}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 24 }} className="message-bubble">
      <BotAvatar />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: 12.5, fontWeight: 700, color: "#fff" }}>GopherGPT</span>
        </div>
        {message && (
          <div
            className={`bot-message${content.length ? " mb-3" : ""}`}
            dangerouslySetInnerHTML={{ __html: formatBotMessage(message) }}
          />
        )}
        {content.length > 0 && <RichContent content={content} />}
      </div>
    </div>
  );
};
