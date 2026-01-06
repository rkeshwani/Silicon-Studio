import { useState, useEffect } from 'react'
import { DataPreparation } from './components/DataPreparation'
import { MemoryTetris } from './components/MemoryTetris'
import { MemoryTetrisMini } from './components/MemoryTetrisMini'
import { ChatInterface } from './components/ChatInterface'
import { EngineInterface } from './components/EngineInterface'

import { ModelsInterface } from './components/ModelsInterface'

function App() {
  const [activeTab, setActiveTab] = useState('models')
  const [hoveredTab, setHoveredTab] = useState<string | null>(null)
  const [backendReady, setBackendReady] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('Initializing backend...')

  const displayedTab = hoveredTab || activeTab

  // Poll backend health until ready
  useEffect(() => {
    let cancelled = false;
    let attempts = 0;

    const checkBackend = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/health');
        if (response.ok && !cancelled) {
          setBackendReady(true);
        }
      } catch {
        // Backend not ready yet
        attempts++;
        if (attempts > 5) {
          setLoadingMessage('Starting MLX engine...');
        }
        if (!cancelled) {
          setTimeout(checkBackend, 500);
        }
      }
    };

    checkBackend();

    return () => { cancelled = true; };
  }, []);

  // Show loading screen while backend starts
  if (!backendReady) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-[rgba(15,15,15,0.95)]">
        <div className="flex flex-col items-center gap-6">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent mb-2">
              Silicon Studio
            </h1>
            <p className="text-sm text-gray-400">{loadingMessage}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-transparent">
      {/* Titlebar / Drag Region */}
      <div className="h-10 w-full drag-region shimmer-bg flex items-center justify-center relative">
        <span className="text-sm font-medium text-gray-400">Silicon Studio</span>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden rounded-bl-lg rounded-br-lg border-t border-white/10 bg-[rgba(30,30,30,0.8)] backdrop-blur-xl">

        {/* Sidebar */}
        <div className="w-64 bg-black/20 flex flex-col p-4 border-r border-white/5 relative z-20">
          <div className="mb-6 px-2">
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">Silicon Studio</h1>
          </div>

          <nav className="space-y-1">
            <SidebarItem
              label="Models"
              active={activeTab === 'models'}
              onClick={() => setActiveTab('models')}
              icon="💾"
            />
            <SidebarItem
              label="Fine-Tuning"
              active={activeTab === 'engine'}
              onClick={() => setActiveTab('engine')}
              icon="🤖"
            />
            <SidebarItem
              label="Chat"
              active={activeTab === 'chat'}
              onClick={() => setActiveTab('chat')}
              icon="💬"
            />

            <div className="pt-4 pb-2">
              <div className="px-2 flex items-center gap-1 group relative w-fit">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Enterprise
                </p>
                <div className="cursor-help text-gray-600 hover:text-gray-400">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3 h-3">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                  </svg>
                </div>
                {/* Tooltip */}
                <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 w-max px-3 py-1.5 bg-black/90 border border-white/10 text-xs text-white rounded-md shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 whitespace-nowrap">
                  Enterprise version coming soon
                </div>
              </div>
            </div>

            <LockedSidebarItem
              label="Data Preparation"
              icon="📊"
              onHover={(isHovering) => setHoveredTab(isHovering ? 'studio' : null)}
            />

            <LockedSidebarItem label="Evaluations" icon="🧪" tooltip="Feature coming soon!" />
            <LockedSidebarItem label="RAG Knowledge" icon="🧠" tooltip="Feature coming soon!" />
            <LockedSidebarItem label="Agent Workflows" icon="⚡" tooltip="Feature coming soon!" />
            <LockedSidebarItem label="Internal Deployment" icon="🚀" tooltip="Feature coming soon!" />

          </nav>

          <div className="flex-1" />

          <MemoryTetrisMini />
        </div>

        <div className="flex-1 overflow-y-auto no-drag relative">
          {hoveredTab && (
            <div className="absolute inset-0 z-50 bg-black/50 backdrop-blur-[1px] flex items-center justify-center pointer-events-none">
              <div className="bg-black/80 border border-white/10 px-4 py-2 rounded-full text-sm font-medium text-white shadow-2xl transform translate-y-[-100px]">
                🔒 Enterprise Feature Preview
              </div>
            </div>
          )}
          <div className={
            displayedTab === 'models' ? "h-full" :
              (displayedTab === 'engine' || displayedTab === 'studio') ? "max-w-7xl mx-auto h-full p-8" :
                "max-w-4xl mx-auto h-full p-8"
          }>
            {displayedTab === 'studio' && <DataPreparation />}
            {displayedTab === 'models' && <ModelsInterface />}
            {displayedTab === 'engine' && (
              <div className="space-y-8">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold">Fine-Tuning Engine</h2>
                  <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded border border-green-500/20">MLX Accelerated</span>
                </div>
                <MemoryTetris />
                <EngineInterface />
              </div>
            )}
            {displayedTab === 'chat' && <ChatInterface />}
          </div>
        </div>

      </div>
    </div>
  )
}

function SidebarItem({ label, active, onClick, icon }: { label: string, active: boolean, onClick: () => void, icon: string }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-all ${active
        ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
        : 'text-gray-400 hover:bg-white/5 hover:text-white'
        }`}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </button>
  )
}

function LockedSidebarItem({ label, icon, onHover, tooltip }: { label: string, icon: string, onHover?: (hovering: boolean) => void, tooltip?: string }) {
  return (
    <div
      className="w-full flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium text-gray-600 cursor-not-allowed opacity-50 select-none group relative hover:opacity-80 transition-opacity"
      onMouseEnter={() => onHover && onHover(true)}
      onMouseLeave={() => onHover && onHover(false)}
    >
      <div className="flex items-center space-x-3">
        <span className="grayscale">{icon}</span>
        <span>{label}</span>
      </div>
      <span className="text-xs opacity-50">🔒</span>

      {tooltip && (
        <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 w-max px-3 py-1.5 bg-black/90 border border-white/10 text-xs text-white rounded-md shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 whitespace-nowrap">
          {tooltip}
        </div>
      )}
    </div>
  )
}

export default App
