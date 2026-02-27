"use client";

import { useState } from "react";
import ChatInput from "@/components/ChatInput";
import ChatMessage from "@/components/ChatMessage";
import BlinkingCursor from "@/components/BlinkingCursor";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  isStreaming?: boolean;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (question: string) => {
    const userMessage: Message = {
      id: crypto.randomUUID(),
      content: question,
      isUser: true,
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Request failed");
      }

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        content: data.answer,
        isUser: false,
        isStreaming: true,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        content: err instanceof Error ? err.message : "Something went wrong.",
        isUser: false,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-bg">
      <header className="shrink-0 py-6 px-4 sm:py-8">
        <h1
          className="text-center text-lg sm:text-xl md:text-2xl font-bold"
          style={{
            background: "linear-gradient(90deg, #00ff41, #00ffff)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            filter: "drop-shadow(0 0 8px rgba(0, 255, 65, 0.6))",
          }}
        >
          MMJ RAGu Academy
        </h1>
      </header>

      <main className="flex-1 overflow-y-auto px-4 pb-4 flex flex-col gap-4">
        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            content={msg.content}
            isUser={msg.isUser}
            isStreaming={msg.isStreaming}
          />
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div
              className="px-4 py-3 rounded border border-accent bg-accent/10"
              style={{
                borderColor: "var(--accent)",
                backgroundColor: "rgba(26, 58, 26, 0.1)",
              }}
            >
              <span className="text-primary text-sm sm:text-base">
                <BlinkingCursor />
              </span>
            </div>
          </div>
        )}
      </main>

      <footer className="shrink-0 p-4 pt-0 pb-[env(safe-area-inset-bottom,0.5rem)]">
        <ChatInput onSubmit={handleSubmit} disabled={isLoading} />
      </footer>
    </div>
  );
}
