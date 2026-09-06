import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, ShieldAlert, Sparkles, ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';
import { assistantAPI } from '../services/api';

const RiskAssistant = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hello. I am the BharatSHIELD AI Risk Assistant. I provide constrained, defense-oriented analysis of transaction risk scores, SHAP explanations, velocity patterns, and active merchant fraud spikes.\n\nAsk me about a transaction (e.g. 'Explain transaction <id>'), today's critical risk holds, or active fraud anomaly alerts.",
      guardrail_status: 'INFO',
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isTyping) return;

    const userQuery = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userQuery }]);
    setIsTyping(true);

    try {
      const res = await assistantAPI.ask(userQuery);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.response,
          guardrail_status: res.guardrail_status,
          grounded_data: res.grounded_data,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Unable to query risk intelligence engine. Please ensure backend is reachable.',
          guardrail_status: 'ERROR',
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const samplePrompts = [
    "Summarize today's critical risks",
    "What are the active fraud alerts?",
    "Explain our core fraud model and features",
    "Can you refund money for a transaction?", // test guardrail!
  ];

  return (
    <div className="p-8 max-w-5xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
            <Bot className="text-emerald-400" size={26} />
            AI Risk Assistant
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Constrained, defense-only query layer over BharatSHIELD risk scores and SHAP telemetry.
          </p>
        </div>

        {/* Security Badge */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
          <ShieldCheck size={14} />
          <span>Strict Read-Only Guardrails Enforced</span>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur flex flex-col overflow-hidden shadow-xl">
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.map((msg, index) => {
            const isUser = msg.role === 'user';
            const isBlocked = msg.guardrail_status === 'BLOCKED';

            return (
              <div
                key={index}
                className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-1 ${
                      isBlocked
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    }`}
                  >
                    {isBlocked ? <AlertCircle size={16} /> : <Bot size={16} />}
                  </div>
                )}

                <div
                  className={`max-w-2xl rounded-2xl p-4 text-sm leading-relaxed whitespace-pre-wrap ${
                    isUser
                      ? 'bg-emerald-600 text-white rounded-br-none shadow-md'
                      : isBlocked
                      ? 'bg-rose-950/40 text-rose-200 border border-rose-500/40 rounded-bl-none'
                      : 'bg-slate-800/80 text-slate-200 border border-slate-700/60 rounded-bl-none'
                  }`}
                >
                  {isBlocked && (
                    <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-rose-400 mb-2 border-b border-rose-500/20 pb-1">
                      <ShieldAlert size={14} /> Defense Guardrail Block
                    </div>
                  )}
                  {msg.content}
                </div>
              </div>
            );
          })}

          {isTyping && (
            <div className="flex gap-3 justify-start items-center">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center justify-center shrink-0">
                <Bot size={16} />
              </div>
              <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl px-4 py-3 text-xs text-slate-400 flex items-center gap-2">
                <RefreshCw size={14} className="animate-spin text-emerald-400" />
                Analyzing risk telemetry and decision logs...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Quick Prompts */}
        <div className="pt-4 border-t border-slate-800/80 mb-3">
          <div className="text-[11px] text-slate-500 uppercase font-bold tracking-wider mb-2">
            Suggested Inquiries:
          </div>
          <div className="flex flex-wrap gap-2">
            {samplePrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setInput(prompt);
                }}
                className="text-xs px-3 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSend} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about transaction risk factors, critical alerts, or explain a specific ID..."
            className="flex-1 bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition font-sans"
          />
          <button
            type="submit"
            disabled={!input.trim() || isTyping}
            className="px-5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl font-semibold flex items-center justify-center transition"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default RiskAssistant;
