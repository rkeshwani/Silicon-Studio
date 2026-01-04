import { useState, useCallback } from 'react'
import { apiClient, type PreviewRow } from '../api/client'

export function DataStudio() {
    const [file, setFile] = useState<File | null>(null)
    const [preview, setPreview] = useState<PreviewRow[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleDrop = useCallback(async (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        const droppedFile = e.dataTransfer.files[0]
        if (droppedFile && droppedFile.name.endsWith('.csv')) {
            setFile(droppedFile)
            setLoading(true)
            setError(null)
            try {
                // In a real Electron app, we'd send the file path.
                // For MVP browser dev, we might mock or use the File object if the backend handled upload.
                // Because our backend expects a file_path string (local file system), 
                // this only works if the backend can access the path (Electron feature).
                // For this demo, we'll assume the file is in the backend directory or pass a dummy path if running in browser
                // OR we use the file.path property which exists in Electron.

                let path = (droppedFile as any).path;
                if (!path) {
                    // Fallback for browser testing - we can't really read local paths in browser
                    // so we'll just simulate with 'test.csv' for the verified backend file
                    console.warn("No file path found (browser mode?), defaulting to 'test.csv'")
                    path = 'test.csv'
                }

                const res = await apiClient.studio.previewCsv(path)
                setPreview(res.data)
            } catch (err: any) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        } else {
            setError("Please drop a valid .csv file")
        }
    }, [])

    const onDragOver = (e: React.DragEvent) => {
        e.preventDefault()
    }

    return (
        <div className="h-full flex flex-col space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold tracking-tight text-white">Data Studio</h2>
                {file && <span className="text-sm text-gray-400 bg-white/5 px-3 py-1 rounded-full">{file.name}</span>}
            </div>

            {/* Drag Drop Zone */}
            {!preview.length && (
                <div
                    onDrop={handleDrop}
                    onDragOver={onDragOver}
                    className={`flex-1 border-2 border-dashed rounded-xl flex flex-col items-center justify-center transition-all ${file ? 'border-green-500/50 bg-green-500/10' : 'border-gray-700 hover:border-blue-500/50 hover:bg-blue-500/5'
                        }`}
                >
                    <div className="text-4xl mb-4 opacity-50">📄</div>
                    <p className="text-gray-400 font-medium">Drag & Drop CSV Dataset</p>
                    <p className="text-xs text-gray-600 mt-2">Supports .csv (Instruction, Input, Output)</p>
                    {error && <p className="text-red-400 text-sm mt-4">{error}</p>}
                    {loading && <p className="text-blue-400 text-sm mt-4 animate-pulse">Processing...</p>}
                </div>
            )}

            {/* Preview Table */}
            {preview.length > 0 && (
                <div className="flex-1 overflow-hidden flex flex-col rounded-xl border border-white/10 bg-black/20">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm text-gray-400">
                            <thead className="bg-white/5 text-gray-200 uppercase font-bold text-xs">
                                <tr>
                                    {Object.keys(preview[0]).map(header => (
                                        <th key={header} className="px-6 py-3">{header}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {preview.map((row, idx) => (
                                    <tr key={idx} className="hover:bg-white/5 transition-colors">
                                        {Object.values(row).map((cell, cIdx) => (
                                            <td key={cIdx} className="px-6 py-4 truncate max-w-[200px]">{cell}</td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <div className="p-4 border-t border-white/10 bg-black/40 flex justify-end space-x-3">
                        <button
                            onClick={() => { setPreview([]); setFile(null); }}
                            className="px-4 py-2 text-xs font-medium text-gray-400 hover:text-white transition-colors"
                        >
                            Cancel
                        </button>
                        <button className="px-4 py-2 text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white rounded shadow-lg shadow-blue-500/20 transition-all">
                            Clean & Save JSONL
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
