import React from 'react'

interface EngineSelectionModalProps {
  onSelect: (engine: string) => void
  hardware: {
    mlx: boolean
    cuda: boolean
    cuda_installable?: boolean
  }
}

export function EngineSelectionModal({ onSelect, hardware }: EngineSelectionModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-[#1e1e1e] border border-white/10 rounded-xl p-8 max-w-2xl w-full shadow-2xl">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent mb-2">
            Select Your Engine
          </h2>
          <p className="text-gray-400">
            Choose the AI engine optimized for your hardware.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* MLX Option */}
          <button
            onClick={() => onSelect('mlx')}
            disabled={!hardware.mlx}
            className={`relative group p-6 rounded-xl border transition-all duration-300 text-left ${
              hardware.mlx
                ? 'border-white/10 hover:border-blue-500/50 hover:bg-white/5 cursor-pointer'
                : 'border-white/5 bg-white/5 opacity-50 cursor-not-allowed'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-2xl">🍏</span>
              {hardware.mlx && (
                <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded-full border border-green-500/20">
                  Detected
                </span>
              )}
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Apple MLX</h3>
            <p className="text-sm text-gray-400">
              Optimized for Apple Silicon (M1/M2/M3/M4). Uses unified memory for high-performance local training.
            </p>
          </button>

          {/* Unsloth Option */}
          <button
            onClick={() => onSelect('unsloth')}
            disabled={!hardware.cuda && !hardware.cuda_installable}
            className={`relative group p-6 rounded-xl border transition-all duration-300 text-left ${
              hardware.cuda || hardware.cuda_installable
                ? 'border-white/10 hover:border-purple-500/50 hover:bg-white/5 cursor-pointer'
                : 'border-white/5 bg-white/5 opacity-50 cursor-not-allowed'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-2xl">🦥</span>
              {hardware.cuda && (
                <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded-full border border-green-500/20">
                  Detected
                </span>
              )}
              {!hardware.cuda && hardware.cuda_installable && (
                <span className="text-xs px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded-full border border-yellow-500/20">
                  Install Available
                </span>
              )}
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Unsloth (CUDA)</h3>
            <p className="text-sm text-gray-400">
              {hardware.cuda_installable && !hardware.cuda 
                ? "Click to automatically install CUDA dependencies and restart the backend." 
                : "Optimized for NVIDIA GPUs. Up to 2x faster fine-tuning and 70% less memory usage."}
            </p>
          </button>
        </div>

        {!hardware.mlx && !hardware.cuda && !hardware.cuda_installable && (
          <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm text-center">
            No compatible hardware detected. Please ensure you have an Apple Silicon Mac or an NVIDIA GPU with drivers installed.
          </div>
        )}
      </div>
    </div>
  )
}
