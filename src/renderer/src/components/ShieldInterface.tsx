import { useState } from 'react'
import { apiClient } from '../api/client'

export function ShieldInterface() {
    const [input, setInput] = useState('')
    const [result, setResult] = useState<any>(null)
    const [loading, setLoading] = useState(false)

    const handleScan = async () => {
        if (!input) return
        setLoading(true)
        try {
            const data = await apiClient.shield.redact(input)
            setResult(data)
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="h-full flex flex-col space-y-6">
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex flex-col space-y-2">
                    <label className="text-sm font-bold text-gray-400">Input Text</label>
                    <textarea
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        placeholder="Paste text containing sensitive PII here (e.g. emails, phone numbers)..."
                        className="flex-1 bg-black/20 border border-white/10 rounded-xl p-4 text-white outline-none focus:border-blue-500 resize-none font-mono text-sm leading-relaxed"
                    />
                </div>

                <div className="flex flex-col space-y-2">
                    <label className="text-sm font-bold text-gray-400">Redacted Output</label>
                    <div className="flex-1 bg-black/40 border border-white/10 rounded-xl p-4 text-gray-300 font-mono text-sm leading-relaxed overflow-y-auto whitespace-pre-wrap">
                        {result ? result.text : <span className="text-gray-600 italic">Scan to see redacted results...</span>}
                    </div>
                </div>
            </div>

            {result && result.items && result.items.length > 0 && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
                    <h4 className="text-red-400 font-bold text-sm mb-3">Detected Entities</h4>
                    <div className="flex flex-wrap gap-2">
                        {result.items.map((item: any, i: number) => (
                            <span key={i} className="px-2 py-1 bg-red-500/20 text-red-300 text-xs rounded border border-red-500/20">
                                {item.entity_type}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            <div className="flex justify-end">
                <button
                    onClick={handleScan}
                    disabled={loading || !input}
                    className="bg-red-600 hover:bg-red-500 text-white font-bold px-6 py-3 rounded-lg shadow-lg shadow-red-500/20 transition-all flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <span>{loading ? 'Scanning...' : 'Scan & Redact PII'}</span>
                    {!loading && <span>🛡️</span>}
                </button>
            </div>
        </div>
    )
}
