import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

export function ModelsInterface() {
    const [models, setModels] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [downloading, setDownloading] = useState<Set<string>>(new Set());
    const [error, setError] = useState<string | null>(null);

    // Custom Model State
    const [showAddModal, setShowAddModal] = useState(false);
    const [customName, setCustomName] = useState("");
    const [customPath, setCustomPath] = useState("");
    const [customUrl, setCustomUrl] = useState("");

    useEffect(() => {
        fetchModels();
    }, []);

    const fetchModels = async (silent = false) => {
        try {
            if (!silent) setLoading(true);
            const data = await apiClient.engine.getModels();
            setModels(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            if (!silent) setLoading(false);
        }
    };

    // Poll for updates if any model is downloading
    useEffect(() => {
        const hasActiveDownloads = models.some(m => m.downloading) || downloading.size > 0;

        if (hasActiveDownloads) {
            const interval = setInterval(() => {
                fetchModels(true);
            }, 2000);
            return () => clearInterval(interval);
        }
    }, [models, downloading]);

    const handleDownload = async (modelId: string) => {
        try {
            setDownloading(prev => new Set(prev).add(modelId));
            await apiClient.engine.downloadModel(modelId);
            // Trigger immediate update to get server-side status
            fetchModels(true);
        } catch (err: any) {
            alert(`Failed to start download: ${err.message}`);
            setDownloading(prev => {
                const next = new Set(prev);
                next.delete(modelId);
                return next;
            });
        }
    };

    const [modelToDelete, setModelToDelete] = useState<any | null>(null);

    const handleDelete = async () => {
        if (!modelToDelete) return;
        try {
            setLoading(true);
            await apiClient.engine.deleteModel(modelToDelete.id);
            await fetchModels(); // Refresh list
            setModelToDelete(null);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async () => {
        if (!customName || !customPath) return;
        try {
            setLoading(true);
            await apiClient.engine.registerModel(customName, customPath, customUrl);
            await fetchModels();
            setShowAddModal(false);
            setCustomName("");
            setCustomPath("");
            setCustomUrl("");
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="h-full flex flex-col p-6 space-y-6 overflow-y-auto relative">
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-semibold tracking-tight text-white mb-2">Model Library</h1>
                    <p className="text-white/60">Manage your local LLM weights via Hugging Face.</p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add Foundation Model
                </button>
            </header>

            {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg text-sm flex justify-between items-center">
                    <span>{error}</span>
                    <button onClick={() => setError(null)} className="text-white/40 hover:text-white">✕</button>
                </div>
            )}

            {loading && models.length === 0 ? (
                <div className="text-white/40">Loading models...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {models.map((model) => {
                        // Check both local state (for immediate feedback) and server state (for persistence/refresh)
                        const isDownloading = downloading.has(model.id) || model.downloading;
                        const isDownloaded = model.downloaded;

                        return (
                            <div
                                key={model.id}
                                className="bg-[#1E1E1E] border border-white/5 rounded-xl p-5 flex flex-col gap-4 hover:border-white/10 transition-colors relative group"
                            >
                                <div className="flex-1 pr-8">
                                    <div className="flex items-start justify-between mb-2">
                                        <span className={`text-xs font-medium px-2 py-1 rounded bg-white/10 text-white/80 ${model.is_custom ? 'bg-purple-500/20 text-purple-300' : ''}`}>
                                            {model.family || (model.is_custom ? 'Custom' : 'LLM')}
                                        </span>
                                        <span className="text-xs text-white/40 font-mono">
                                            {model.size}
                                        </span>
                                    </div>
                                    <h3 className="text-lg font-medium text-white mb-1 truncate" title={model.name}>
                                        {model.name}
                                    </h3>
                                    <p className="text-xs text-white/50 truncate font-mono" title={model.id}>
                                        {model.id}
                                    </p>
                                </div>

                                <div className="pt-4 border-t border-white/5">
                                    {isDownloaded ? (
                                        <div className="flex gap-2">
                                            <button
                                                disabled
                                                className="flex-1 py-2 px-4 rounded-lg bg-green-500/10 text-green-400 text-sm font-medium border border-green-500/20 cursor-default flex items-center justify-center gap-2"
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                </svg>
                                                Installed
                                            </button>
                                            <button
                                                onClick={() => setModelToDelete(model)}
                                                className="px-3 py-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20 transition-colors"
                                                title="Delete Model"
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                        </div>
                                    ) : (
                                        <button
                                            onClick={() => handleDownload(model.id)}
                                            disabled={isDownloading}
                                            className={`w-full py-2 px-4 rounded-lg text-sm font-medium transition-all ${isDownloading
                                                ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20 cursor-wait'
                                                : 'bg-white text-black hover:bg-gray-100'
                                                }`}
                                        >
                                            {isDownloading ? (
                                                <span className="flex items-center justify-center gap-2">
                                                    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                    </svg>
                                                    Downloading...
                                                </span>
                                            ) : (
                                                "Download Model"
                                            )}
                                        </button>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Confirmation Modal */}
            {modelToDelete && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                    <div className="bg-[#1E1E1E] border border-white/10 rounded-xl max-w-sm w-full p-6 shadow-2xl transform transition-all scale-100">
                        <h3 className="text-lg font-bold text-white mb-2">Delete Model?</h3>
                        <p className="text-gray-400 text-sm mb-6">
                            Are you sure you want to delete <span className="text-white font-medium">{modelToDelete.name}</span>?
                            This will remove the downloaded files ({modelToDelete.size}) from your disk.
                        </p>
                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setModelToDelete(null)}
                                className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:bg-white/5 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleDelete}
                                className="px-4 py-2 rounded-lg text-sm font-medium bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/20 transition-all"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Add Foundation Model Modal */}
            {showAddModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                    <div className="bg-[#1E1E1E] border border-white/10 rounded-xl max-w-md w-full p-6 shadow-2xl transform transition-all scale-100">
                        <h3 className="text-lg font-bold text-white mb-4">Add Foundation Model</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs uppercase text-gray-500 font-semibold mb-1">Model Name</label>
                                <input
                                    type="text"
                                    value={customName}
                                    onChange={(e) => setCustomName(e.target.value)}
                                    placeholder="e.g. My Llama Finetune"
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white outline-none focus:border-blue-500 text-sm"
                                />
                            </div>

                            <div>
                                <label className="block text-xs uppercase text-gray-500 font-semibold mb-1">Hugging Face URL (Optional)</label>
                                <input
                                    type="text"
                                    value={customUrl}
                                    onChange={(e) => setCustomUrl(e.target.value)}
                                    placeholder="https://huggingface.co/..."
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white outline-none focus:border-blue-500 text-sm"
                                />
                                <p className="text-[10px] text-white/30 mt-1">For reference only.</p>
                            </div>

                            <div>
                                <label className="block text-xs uppercase text-gray-500 font-semibold mb-1">Model Folder Path</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={customPath}
                                        readOnly
                                        placeholder="/path/to/extracted/model"
                                        className="flex-1 bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white outline-none focus:border-blue-500 text-sm opacity-70"
                                    />
                                    <button
                                        onClick={async () => {
                                            const path = await (window as any).electronAPI.selectDirectory();
                                            if (path) setCustomPath(path);
                                        }}
                                        className="bg-white/10 hover:bg-white/20 text-white px-3 py-2 rounded-lg transition-colors text-sm"
                                    >
                                        📂
                                    </button>
                                </div>
                                <p className="text-[10px] text-white/40 mt-1">
                                    This absolute path will be used as the <strong>Model ID</strong> by MLX.
                                    Ensure it contains <code>config.json</code> and <code>*.safetensors</code>.
                                </p>
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 mt-6">
                            <button
                                onClick={() => setShowAddModal(false)}
                                className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:bg-white/5 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleRegister}
                                disabled={!customName || !customPath || loading}
                                className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
                            >
                                Register Model
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
