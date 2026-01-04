import { useState } from 'react'
import { DataPreparation } from './components/DataPreparation'
import { MemoryTetris } from './components/MemoryTetris'
import { MemoryTetrisMini } from './components/MemoryTetrisMini'
import { ChatInterface } from './components/ChatInterface'
import { EngineInterface } from './components/EngineInterface'

import { ModelsInterface } from './components/ModelsInterface'

function App() {
  const [activeTab, setActiveTab] = useState('studio')

  return (
    <div className="h-screen w-screen flex flex-col bg-transparent">
      {/* Titlebar / Drag Region */}
      <div className="h-10 w-full drag-region shimmer-bg flex items-center justify-center relative">
        <span className="text-sm font-medium text-gray-400">Silicon Studio</span>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden rounded-bl-lg rounded-br-lg border-t border-white/10 bg-[rgba(30,30,30,0.8)] backdrop-blur-xl">

        {/* Sidebar */}
        <div className="w-64 bg-black/20 flex flex-col p-4 border-r border-white/5">
          <div className="mb-6 px-2">
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">Silicon Studio</h1>
          </div>

          <nav className="space-y-1">
            <SidebarItem
              label="Data Preparation"
              active={activeTab === 'studio'}
              onClick={() => setActiveTab('studio')}
              icon="📊"
            />
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
          </nav>

          <div className="flex-1" />

          <MemoryTetrisMini />
        </div>

        <div className="flex-1 overflow-y-auto no-drag">
          <div className={
            activeTab === 'models' ? "h-full" :
              (activeTab === 'engine' || activeTab === 'studio') ? "max-w-7xl mx-auto h-full p-8" :
                "max-w-4xl mx-auto h-full p-8"
          }>
            {activeTab === 'studio' && <DataPreparation />}
            {activeTab === 'models' && <ModelsInterface />}
            {activeTab === 'engine' && (
              <div className="space-y-8">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold">Fine-Tuning Engine</h2>
                  <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded border border-green-500/20">MLX Accelerated</span>
                </div>
                <MemoryTetris />
                <EngineInterface />
              </div>
            )}
            {activeTab === 'chat' && <ChatInterface />}
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

export default App
