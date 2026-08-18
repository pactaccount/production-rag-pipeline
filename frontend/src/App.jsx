import React, { useState, useRef, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial } from '@react-three/drei';
import * as random from 'maath/random/dist/maath-random.esm';
import axios from 'axios';
import { Settings, Upload, Send, MessageSquare, Loader2, Key } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';

// 3D Background Component
function ParticleBackground(props) {
  const ref = useRef();
  const [sphere] = useState(() => random.inSphere(new Float32Array(5000), { radius: 1.5 }));
  
  useFrame((state, delta) => {
    ref.current.rotation.x -= delta / 500;
    ref.current.rotation.y -= delta / 1000;
  });

  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      <Points ref={ref} positions={sphere} stride={3} frustumCulled={false} {...props}>
        <PointMaterial transparent color="#3b82f6" size={0.005} sizeAttenuation={true} depthWrite={false} />
      </Points>
    </group>
  );
}

// In production (Render), the backend and frontend share the same domain.
// By using a relative path, the browser automatically prepends the correct domain (e.g., https://nexus-ai.onrender.com/api)
const API_BASE_URL = '/api';

const PROVIDERS = ["Gemini", "Groq", "Anthropic", "OpenAI", "Mistral", "Cohere", "Together", "Fireworks"];
const DEFAULT_MODELS = {
    "Gemini": "models/gemini-2.5-flash", 
    "Groq": "llama3-70b-8192", 
    "Anthropic": "claude-3-haiku-20240307", 
    "OpenAI": "gpt-3.5-turbo",
    "Mistral": "mistral-large-latest",
    "Cohere": "command-r-plus",
    "Together": "meta-llama/Llama-3-70b-chat-hf",
    "Fireworks": "accounts/fireworks/models/mixtral-8x7b-instruct"
};

export default function App() {
  const [sessionId] = useState(() => uuidv4());
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  
  // Settings State
  const [useDefaultKeys, setUseDefaultKeys] = useState(true);
  const [provider, setProvider] = useState('Gemini');
  const [modelName, setModelName] = useState(DEFAULT_MODELS['Gemini']);
  const [apiKey, setApiKey] = useState('');

  // Upload State
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  // Handlers
  const handleProviderChange = (e) => {
    const p = e.target.value;
    setProvider(p);
    setModelName(DEFAULT_MODELS[p]);
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus('');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    try {
      await axios.post(`${API_BASE_URL}/ingest`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadStatus('Document uploaded successfully!');
    } catch (error) {
      setUploadStatus('Failed to upload document.');
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    const newHistory = [...messages, userMessage];
    setMessages(newHistory);
    setInput('');
    setIsLoading(true);

    try {
      const payload = {
        query: userMessage.content,
        session_id: sessionId,
        provider: useDefaultKeys ? null : provider,
        model_name: useDefaultKeys ? null : modelName,
        api_key: useDefaultKeys ? null : apiKey,
        chat_history: messages
      };

      const response = await axios.post(`${API_BASE_URL}/chat`, payload);
      setMessages([...newHistory, { role: 'assistant', content: response.data.response }]);
    } catch (error) {
      setMessages([...newHistory, { role: 'assistant', content: 'Sorry, there was an error processing your request.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-screen h-screen bg-black text-slate-200 overflow-hidden relative font-sans">
      {/* 3D Background */}
      <div className="absolute inset-0 z-0 opacity-60">
        <Canvas camera={{ position: [0, 0, 1] }}>
          <ParticleBackground />
        </Canvas>
      </div>

      {/* Main UI */}
      <div className="absolute inset-0 z-10 flex flex-col items-center justify-center p-4">
        
        {/* Header */}
        <header className="w-full max-w-6xl flex justify-between items-center mb-6 px-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.5)]">
              <MessageSquare className="text-white w-6 h-6" />
            </div>
          </div>
          <button 
            onClick={() => setShowSettings(true)}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700 rounded-full backdrop-blur-md transition-all text-sm font-medium"
          >
            <Settings className="w-4 h-4" />
            Settings
          </button>
        </header>

        {/* Chat Container */}
        <div className="w-full max-w-6xl h-[85vh] flex flex-col bg-slate-900/60 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl overflow-hidden">
          
          {/* File Upload Banner */}
          <div className="w-full bg-slate-800/50 border-b border-slate-700/50 p-4 flex items-center justify-between">
            <div className="text-sm text-slate-400">
              {uploadStatus || "Upload a document to start chatting."}
            </div>
            <div>
              <input type="file" className="hidden" ref={fileInputRef} onChange={handleUpload} accept="application/pdf" />
              <button 
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                {isUploading ? 'Uploading...' : 'Upload PDF'}
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
            {messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
                <MessageSquare className="w-12 h-12 mb-4 opacity-50" />
                <p>Hello! Ask me anything about your uploaded documents.</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-2xl px-5 py-3 ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-800/80 border border-slate-700 text-slate-200 shadow-lg'}`}>
                    {msg.content}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-800/80 border border-slate-700 rounded-2xl px-5 py-3 flex items-center gap-3">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                  <span className="text-sm text-slate-400">Assistant is thinking...</span>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <form onSubmit={handleSend} className="p-4 bg-slate-900/80 border-t border-slate-700/50">
            <div className="relative flex items-center">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                className="w-full bg-slate-800 border border-slate-700 rounded-full pl-6 pr-14 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-slate-200 placeholder-slate-500 shadow-inner"
              />
              <button 
                type="submit" 
                disabled={isLoading || !input.trim()}
                className="absolute right-2 w-10 h-10 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 rounded-full flex items-center justify-center transition-colors shadow-lg"
              >
                <Send className="w-4 h-4 text-white ml-1" />
              </button>
            </div>
          </form>

        </div>
      </div>

      {/* Settings Modal Overlay */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
              <Settings className="w-5 h-5 text-blue-400" />
              System Settings
            </h2>
            
            <div className="mb-6 bg-slate-800/50 p-4 rounded-xl border border-slate-700">
              <label className="flex items-center gap-3 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={useDefaultKeys} 
                  onChange={(e) => setUseDefaultKeys(e.target.checked)}
                  className="w-5 h-5 rounded border-slate-600 text-blue-500 focus:ring-blue-500/50 bg-slate-700"
                />
                <span className="font-medium">Use Server Default Keys</span>
              </label>
              <p className="text-xs text-slate-400 mt-2 ml-8">
                If checked, you don't need an API key. We will route your requests through the server's default Gemini tier.
              </p>
            </div>

            <div className={`transition-all duration-300 ${useDefaultKeys ? 'opacity-30 pointer-events-none blur-[1px]' : 'opacity-100'}`}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">LLM Provider</label>
                  <select 
                    value={provider} 
                    onChange={handleProviderChange}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  >
                    {PROVIDERS.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">Model Name</label>
                  <input 
                    type="text" 
                    value={modelName} 
                    onChange={(e) => setModelName(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1 flex items-center gap-2">
                    <Key className="w-3 h-3" /> API Key
                  </label>
                  <input 
                    type="password" 
                    value={apiKey} 
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={`Enter ${provider} API Key`}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm font-mono"
                  />
                </div>
              </div>
            </div>

            <button 
              onClick={() => setShowSettings(false)}
              className="mt-8 w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors"
            >
              Save & Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
