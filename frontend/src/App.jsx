import React, { useState, useRef, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial } from '@react-three/drei';
import * as random from 'maath/random/dist/maath-random.esm';
import axios from 'axios';
import { Settings, Upload, Send, MessageSquare, Loader2, Key, CheckCircle } from 'lucide-react';
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
  const [isDocumentReady, setIsDocumentReady] = useState(false);
  
  // Settings State
  const [useDefaultKeys, setUseDefaultKeys] = useState(true);
  const [provider, setProvider] = useState('Gemini');
  const [modelName, setModelName] = useState(DEFAULT_MODELS['Gemini']);
  const [apiKey, setApiKey] = useState('');

  // Upload State
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState(false);

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
    setUploadStatus('Processing document...');
    setUploadSuccess(false);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    try {
      await axios.post(`${API_BASE_URL}/ingest`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadStatus('Document uploaded and processed successfully!');
      setUploadSuccess(true);
      
      // Transition to chat UI after a brief delay
      setTimeout(() => {
        setIsDocumentReady(true);
      }, 1500);
      
    } catch (error) {
      setUploadStatus('Failed to upload document. Please try again.');
      setUploadSuccess(false);
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
      const errorMsg = error.response?.data?.detail || error.message || 'Sorry, there was an error processing your request.';
      setMessages([...newHistory, { role: 'assistant', content: `Error: ${errorMsg}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-screen h-screen bg-black text-slate-200 overflow-hidden relative font-sans">
      {/* 3D Background */}
      <div className="absolute inset-0 z-0 opacity-40">
        <Canvas camera={{ position: [0, 0, 1] }}>
          <ParticleBackground />
        </Canvas>
      </div>

      {/* Main UI */}
      <div className="absolute inset-0 z-10 flex flex-col items-center p-6">
        
        {/* Header */}
        <header className="w-full max-w-6xl flex justify-between items-center mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-black border border-slate-700 rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(255,255,255,0.1)]">
              <MessageSquare className="text-white w-5 h-5" />
            </div>
            <span className="font-bold text-lg tracking-wide text-white">NEXUS AI</span>
          </div>
          <button 
            onClick={() => setShowSettings(true)}
            className="flex items-center gap-2 px-4 py-2 bg-black hover:bg-slate-900 border border-slate-800 rounded-full backdrop-blur-md transition-all text-sm font-medium text-slate-300"
          >
            <Settings className="w-4 h-4" />
            Settings
          </button>
        </header>

        {!isDocumentReady ? (
          /* Initial Upload Window */
          <div className="flex-1 w-full flex items-center justify-center">
            <div className="w-full max-w-xl bg-black/80 backdrop-blur-2xl border border-slate-800 rounded-3xl shadow-2xl p-10 flex flex-col items-center text-center transform transition-all">
              <div className="w-20 h-20 bg-slate-900 rounded-full flex items-center justify-center mb-8 border border-slate-800 shadow-[0_0_30px_rgba(59,130,246,0.15)]">
                <Upload className="w-8 h-8 text-blue-500" />
              </div>
              <h1 className="text-3xl font-bold mb-3 text-white">Document Intelligence</h1>
              <p className="text-slate-400 mb-10 leading-relaxed">
                Upload your financial documents, SEC 10-K filings, or any PDF to start a secure, multimodal AI analysis session.
              </p>
              
              <div className="w-full">
                <input type="file" className="hidden" ref={fileInputRef} onChange={handleUpload} accept="application/pdf" />
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading || uploadSuccess}
                  className={`w-full py-4 rounded-xl text-lg font-medium transition-all flex items-center justify-center gap-3 shadow-lg
                    ${uploadSuccess 
                      ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-800/50 cursor-default' 
                      : isUploading 
                        ? 'bg-slate-800 text-slate-300 border border-slate-700 cursor-wait'
                        : 'bg-white text-black hover:bg-slate-200 border border-transparent shadow-[0_0_20px_rgba(255,255,255,0.1)]'
                    }`}
                >
                  {uploadSuccess ? (
                    <CheckCircle className="w-6 h-6" />
                  ) : isUploading ? (
                    <Loader2 className="w-6 h-6 animate-spin" />
                  ) : (
                    <Upload className="w-6 h-6" />
                  )}
                  {uploadSuccess ? 'Ready to Chat' : isUploading ? 'Processing Document...' : 'Select PDF Document'}
                </button>
              </div>
              {uploadStatus && (
                <div className={`mt-5 text-sm font-medium ${uploadSuccess ? 'text-emerald-400' : isUploading ? 'text-blue-400 animate-pulse' : 'text-red-400'}`}>
                  {uploadStatus}
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Chat Container */
          <div className="w-full max-w-6xl flex-1 flex flex-col bg-black/80 backdrop-blur-2xl border border-slate-800 rounded-3xl shadow-2xl overflow-hidden mb-4">
            
            {/* Header / Active Document Banner */}
            <div className="w-full bg-slate-900/50 border-b border-slate-800 p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] animate-pulse"></div>
                <span className="text-sm font-medium text-slate-300">Document Active & Ready</span>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 custom-scrollbar">
              {messages.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
                  <MessageSquare className="w-12 h-12 mb-4 opacity-30" />
                  <p className="text-lg">Ask me anything about your uploaded document.</p>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-2xl px-6 py-4 text-[15px] leading-relaxed shadow-lg
                      ${msg.role === 'user' 
                        ? 'bg-slate-200 text-black rounded-tr-sm font-medium' 
                        : 'bg-slate-900 border border-slate-800 text-slate-300 rounded-tl-sm'}`}>
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-sm px-6 py-4 flex items-center gap-3 shadow-lg">
                    <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
                    <span className="text-sm text-slate-400 font-medium">Analyzing...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Input Area */}
            <form onSubmit={handleSend} className="p-5 bg-black border-t border-slate-800">
              <div className="relative flex items-center max-w-4xl mx-auto">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question about the document..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-full pl-6 pr-16 py-4 focus:outline-none focus:ring-1 focus:ring-slate-600 transition-all text-slate-200 placeholder-slate-500 shadow-inner text-[15px]"
                />
                <button 
                  type="submit" 
                  disabled={isLoading || !input.trim()}
                  className="absolute right-2 w-10 h-10 bg-slate-200 hover:bg-white disabled:bg-slate-800 disabled:text-slate-600 text-black rounded-full flex items-center justify-center transition-all shadow-md"
                >
                  <Send className="w-4 h-4 ml-0.5" />
                </button>
              </div>
            </form>

          </div>
        )}
      </div>

      {/* Settings Modal Overlay */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
          <div className="bg-black border border-slate-800 rounded-3xl w-full max-w-md p-8 shadow-2xl relative">
            <h2 className="text-xl font-bold mb-8 flex items-center gap-3 text-white">
              <Settings className="w-5 h-5" />
              System Settings
            </h2>
            
            <div className="mb-6 bg-slate-900 p-5 rounded-2xl border border-slate-800">
              <label className="flex items-center gap-3 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={useDefaultKeys} 
                  onChange={(e) => setUseDefaultKeys(e.target.checked)}
                  className="w-5 h-5 rounded border-slate-700 text-blue-500 focus:ring-blue-500/50 bg-black"
                />
                <span className="font-medium text-slate-200">Use Server Default Keys</span>
              </label>
              <p className="text-xs text-slate-500 mt-2 ml-8 leading-relaxed">
                If checked, you don't need an API key. We will route your requests through the server's default Gemini tier.
              </p>
            </div>

            <div className={`transition-all duration-300 ${useDefaultKeys ? 'opacity-30 pointer-events-none blur-[1px]' : 'opacity-100'}`}>
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">LLM Provider</label>
                  <select 
                    value={provider} 
                    onChange={handleProviderChange}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3.5 focus:outline-none focus:border-slate-600 text-slate-200"
                  >
                    {PROVIDERS.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">Model Name</label>
                  <input 
                    type="text" 
                    value={modelName} 
                    onChange={(e) => setModelName(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3.5 focus:outline-none focus:border-slate-600 text-slate-200 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2 flex items-center gap-2">
                    <Key className="w-3 h-3" /> API Key
                  </label>
                  <input 
                    type="password" 
                    value={apiKey} 
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={`Enter ${provider} API Key`}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3.5 focus:outline-none focus:border-slate-600 text-slate-200 text-sm font-mono"
                  />
                </div>
              </div>
            </div>

            <button 
              onClick={() => setShowSettings(false)}
              className="mt-8 w-full py-4 bg-white text-black hover:bg-slate-200 rounded-xl font-bold transition-colors"
            >
              Save & Close
            </button>
          </div>
        </div>
      )}
      
      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: #334155;
          border-radius: 10px;
        }
      `}} />
    </div>
  );
}
