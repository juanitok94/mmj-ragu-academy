"use client";

import { useEffect, useState } from "react";

interface ChatMessageProps {
  content: string;
  isUser: boolean;
  isStreaming?: boolean;
}

export default function ChatMessage({
  content,
  isUser,
  isStreaming = false,
}: ChatMessageProps) {
  const [displayedContent, setDisplayedContent] = useState("");
  const [isComplete, setIsComplete] = useState(!isStreaming);

  useEffect(() => {
    if (!isStreaming) {
      setDisplayedContent(content);
      setIsComplete(true);
      return;
    }

    setDisplayedContent("");
    setIsComplete(false);
    let index = 0;

    const timer = setInterval(() => {
      if (index < content.length) {
        setDisplayedContent(content.slice(0, index + 1));
        index++;
      } else {
        setIsComplete(true);
        clearInterval(timer);
      }
    }, 30);

    return () => clearInterval(timer);
  }, [content, isStreaming]);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} w-full`}>
      <div
        className={`max-w-[85%] sm:max-w-[75%] px-4 py-3 rounded border`}
        style={{
          borderColor: isUser ? "rgba(26, 58, 26, 0.5)" : "#1a3a1a",
          backgroundColor: isUser ? "rgba(26, 58, 26, 0.2)" : "rgba(26, 58, 26, 0.1)",
        }}
      >
        <p
          className="text-sm sm:text-base break-words whitespace-pre-wrap"
          style={{ color: "#00ff41" }}
        >
          {displayedContent}
          {!isComplete && (
            <span style={{ color: "#00ff41" }} className="inline-block animate-blink ml-0.5">
              |
            </span>
          )}
        </p>
      </div>
    </div>
  );
}
