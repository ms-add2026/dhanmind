import { useState, useRef, useEffect } from "react";
import axios from "axios";

const API_URL = "http://localhost:8000/api/chat/";

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  pathUsed?: string;
  toolResult?: Record<string, unknown> | null;
}

const PATH_LABELS: Record<string, { label: string; color: string }> = {
  stock: {
    label: "MCP · Stock Tool",
    color: "text-amber-700 bg-amber-50 border border-amber-200",
  },
  kb: {
    label: "Local KB · Private Data",
    color: "text-teal-700 bg-teal-50 border border-teal-200",
  },
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      role: "assistant",
      content:
        "Hi! I'm DhanMind — your personal finance copilot. Ask me about stock prices or your account balances.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = {
      id: Date.now(),
      role: "user",
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post(API_URL, { message: text });
      const { answer, path_used, tool_result } = res.data;
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: answer,
          pathUsed: path_used,
          toolResult: tool_result,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content:
            "Something went wrong. Make sure backend and MCP server are running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div
        className="w-full max-w-2xl flex flex-col bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden"
        style={{ height: "85vh" }}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center">
            <span className="text-white text-sm font-bold">D</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-gray-900">DhanMind</h1>
            <p className="text-xs text-gray-400">
              Local-first financial copilot
            </p>
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-teal-400"></span>
            <span className="text-xs text-gray-400">Local · Private</span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div className="max-w-[80%] space-y-1.5">
                <div
                  className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${
                    msg.role === "user"
                      ? "bg-teal-600 text-white rounded-br-sm"
                      : "bg-gray-100 text-gray-800 rounded-bl-sm"
                  }`}
                >
                  {msg.content}
                </div>

                {/* Path badge */}
                {msg.pathUsed && PATH_LABELS[msg.pathUsed] && (
                  <span
                    className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium ${
                      PATH_LABELS[msg.pathUsed].color
                    }`}
                  >
                    {PATH_LABELS[msg.pathUsed].label}
                  </span>
                )}

                {/* Raw tool result */}
                {msg.toolResult && (
                  <details className="text-xs text-gray-400 cursor-pointer">
                    <summary className="hover:text-gray-600">
                      Raw tool result
                    </summary>
                    <pre className="mt-1 p-2 bg-gray-50 rounded-lg overflow-x-auto text-gray-500 border border-gray-100">
                      {JSON.stringify(msg.toolResult, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          ))}

          {/* Loading dots */}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-2.5">
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 150}ms` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-4 py-3 border-t border-gray-100">
          <div className="flex items-center gap-2 bg-gray-50 rounded-xl border border-gray-200 px-3 py-2">
            <textarea
              className="flex-1 bg-transparent text-sm text-gray-800 placeholder-gray-400 resize-none outline-none"
              rows={1}
              placeholder='Try: "What is AAPL trading at?" or "What is my savings balance?"'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="w-8 h-8 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:bg-gray-200 disabled:cursor-not-allowed flex items-center justify-center transition-colors flex-shrink-0"
            >
              <svg
                className="w-4 h-4 text-white"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path
                  d="M22 2L11 13M22 2L15 22L11 13L2 9L22 2Z"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
          <p className="text-center text-xs text-gray-300 mt-2">
            All personal data stays local · Enter to send
          </p>
        </div>
      </div>
    </div>
  );
}