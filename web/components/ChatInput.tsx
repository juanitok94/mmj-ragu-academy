"use client";

import { useState, FormEvent } from "react";

interface ChatInputProps {
  onSubmit: (question: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSubmit,
  disabled = false,
  placeholder = "Ask about My Morning Jacket...",
}: ChatInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (trimmed && !disabled) {
      onSubmit(trimmed);
      setValue("");
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{ width: "100%" }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          width: "100%",
          backgroundColor: "#111111",
          border: "1px solid #1a3a1a",
          borderRadius: "4px",
          padding: "12px 16px",
          gap: "8px",
          alignItems: "center",
        }}
      >
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          style={{
            flex: 1,
            minWidth: 0,
            backgroundColor: "transparent",
            color: "#00ff41",
            border: "none",
            outline: "none",
            fontSize: "14px",
            minHeight: "44px",
          }}
          aria-label="Ask a question"
          autoComplete="off"
          data-chat-input
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          style={{
            flexShrink: 0,
            padding: "8px 16px",
            borderRadius: "4px",
            color: "#00ff41",
            border: "1px solid #1a3a1a",
            backgroundColor: "transparent",
            fontSize: "14px",
            minHeight: "44px",
            cursor: disabled || !value.trim() ? "not-allowed" : "pointer",
            opacity: disabled || !value.trim() ? 0.5 : 1,
          }}
        >
          Ask
        </button>
      </div>
      <style>{`input[data-chat-input]::placeholder { color: rgba(0, 255, 65, 0.4); }`}</style>
    </form>
  );
}
