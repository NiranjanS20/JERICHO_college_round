import React, { useState } from 'react';
import { ShieldCheck, Search, AlertCircle, CheckCircle } from 'lucide-react';

export const Integrity: React.FC = () => {
  const [runId, setRunId] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleVerify = async () => {
    if (!runId) return;
    try {
      const res = await fetch(`/api/integrity/${runId}`);
      setResult(await res.json());
    } catch (e) {
      setResult({ valid: false, reason: "Fetch error" });
    }
  };

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-xl bg-cardBg border border-cardBorder shadow-sm">
        <h2 className="text-xl font-heading font-bold text-textMain flex items-center gap-2 mb-2">
          <ShieldCheck className="w-5 h-5 text-[#275992]" /> 
          Evidence Integrity Verification
        </h2>
        <p className="text-sm text-textMain/70 mb-6">
          Verify the hash chain and HMAC seal of a specific trace run to ensure it hasn't been tampered with.
        </p>

        <div className="flex gap-4 mb-6">
          <input 
            value={runId} 
            onChange={e => setRunId(e.target.value)} 
            placeholder="Enter Trace Run ID..." 
            className="px-4 py-2.5 rounded-lg bg-appBg border border-cardBorder flex-1 focus:outline-none focus:border-[#275992]" 
          />
          <button 
            onClick={handleVerify} 
            className="px-6 py-2.5 bg-[#275992] hover:bg-[#1f4a7c] text-white rounded-lg font-semibold flex items-center gap-2 transition-colors"
          >
            <Search className="w-4 h-4"/> Verify
          </button>
        </div>
        
        {result && (
          <div className="p-4 rounded-lg bg-appBg border border-cardBorder">
            {result.valid ? (
              <p className="text-green-700 font-semibold flex items-center gap-2">
                <CheckCircle className="w-5 h-5"/> {result.details}
              </p>
            ) : (
              <p className="text-red-600 font-semibold flex items-center gap-2">
                <AlertCircle className="w-5 h-5"/> {result.reason}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
