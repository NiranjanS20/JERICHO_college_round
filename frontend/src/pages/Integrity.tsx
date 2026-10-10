import React, { useState, useEffect } from 'react';
import { ShieldCheck, Search, AlertCircle, CheckCircle, Lock, RefreshCw, Key, Link2, FileCheck } from 'lucide-react';
import { fetchIntegrity } from '../api/client';

interface IntegrityProps {
  initialRunId?: string;
}

export const Integrity: React.FC<IntegrityProps> = ({ initialRunId }) => {
  const [runId, setRunId] = useState(initialRunId || '');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const executeVerify = async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    try {
      const data = await fetchIntegrity(id.trim());
      setResult(data);
    } catch (e: any) {
      setResult({
        valid: false,
        status: 'ERROR',
        reason: e.message || 'Failed to communicate with Integrity verification service.',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const urlParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
    const target = initialRunId || urlParams?.get('run');
    if (target) {
      setRunId(target);
      executeVerify(target);
    }
  }, [initialRunId]);

  const handleVerify = () => {
    executeVerify(runId);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="p-6 rounded-2xl bg-white border border-[#95A1D8]/20 shadow-sm">
        <div className="flex items-center justify-between gap-4 mb-2">
          <h2 className="text-xl font-heading font-bold text-[#132E4F] flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-[#275992]" /> 
            Auditor Evidence Integrity Verification
          </h2>
          <span className="px-2.5 py-1 text-[11px] font-bold rounded-full bg-amber-500/10 text-amber-700 border border-amber-500/20">
            PHASE 5: CRYPTOGRAPHIC SEAL
          </span>
        </div>
        
        <p className="text-sm text-[#586D85] mb-6 leading-relaxed">
          Verify the immutable HMAC-SHA256 seal and event hash-chain for any attack trace run. 
          Auditors can independently confirm that execution telemetry has not been tampered with or retroactively rewritten.
        </p>

        {/* Input & Action */}
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <div className="relative flex-1">
            <input 
              value={runId} 
              onChange={e => setRunId(e.target.value)} 
              onKeyDown={e => e.key === 'Enter' && handleVerify()}
              placeholder="Enter Trace Run ID (e.g., atk-8f3a2d91 or run-101)..." 
              className="w-full px-4 py-2.5 rounded-xl bg-[#FFFDF8] border border-[#95A1D8]/30 font-mono text-xs sm:text-sm text-[#132E4F] focus:outline-none focus:border-[#275992] shadow-inner" 
            />
          </div>
          <button 
            onClick={handleVerify}
            disabled={loading || !runId.trim()}
            className="px-6 py-2.5 bg-[#275992] hover:bg-[#1E4775] disabled:opacity-50 text-white rounded-xl font-semibold flex items-center justify-center gap-2 transition-all shadow-sm text-sm"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4"/>}
            <span>Verify Seal</span>
          </button>
        </div>

        {/* Auditor Demo Shortcuts */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-gray-100 text-xs text-[#586D85]">
          <span className="font-semibold text-[#132E4F]">Auditor Test Vectors:</span>
          <button
            onClick={() => {
              setRunId('atk-valid-baseline-001');
              executeVerify('atk-valid-baseline-001');
            }}
            className="px-2.5 py-1 rounded-md bg-gray-100 hover:bg-gray-200 text-[#132E4F] font-mono transition-colors"
          >
            Valid Sealed Trace
          </button>
          <button
            onClick={() => {
              setRunId('atk-tampered-step3');
              executeVerify('atk-tampered-step3');
            }}
            className="px-2.5 py-1 rounded-md bg-red-50 hover:bg-red-100 text-red-700 font-mono transition-colors border border-red-200"
          >
            Tampered Hash Chain (Simulate Breach)
          </button>
        </div>
        
        {/* Verification Report Card */}
        {result && (
          <div className={`mt-6 p-5 rounded-xl border transition-all ${
            result.valid 
              ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950' 
              : 'bg-rose-50/70 border-rose-200 text-rose-950'
          }`}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                {result.valid ? (
                  <CheckCircle className="w-6 h-6 text-emerald-600 mt-0.5 flex-shrink-0" />
                ) : (
                  <AlertCircle className="w-6 h-6 text-rose-600 mt-0.5 flex-shrink-0" />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-base tracking-tight">
                      {result.valid ? 'Cryptographic Integrity Verified' : 'Tamper Detection Alert'}
                    </span>
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                      result.valid ? 'bg-emerald-200 text-emerald-800' : 'bg-rose-200 text-rose-800'
                    }`}>
                      {result.status || (result.valid ? 'VERIFIED' : 'TAMPERED')}
                    </span>
                  </div>

                  <p className="text-xs sm:text-sm mt-1 leading-relaxed opacity-90">
                    {result.details || result.reason}
                  </p>
                </div>
              </div>

              <div className="text-right font-mono text-[11px] opacity-75 hidden sm:block">
                <div>Algorithm: HMAC-SHA256</div>
                <div>Hash Chain: Keccak/SHA-256</div>
              </div>
            </div>

            {result.checkpoint && (
              <div className="mt-4 pt-3 border-t border-emerald-200/60 font-mono text-xs space-y-1 bg-white/60 p-3 rounded-lg">
                <div className="text-emerald-800 font-bold mb-1 flex items-center gap-1.5">
                  <FileCheck className="w-3.5 h-3.5" /> Checkpoint Metadata (Write-Protected)
                </div>
                <div>Trace Run: {result.checkpoint.run_id || result.run_id}</div>
                <div>Events Count: {result.checkpoint.event_count || result.checkpoint.events?.length || 'Recorded'}</div>
                <div className="truncate">Root Hash: {result.checkpoint.root_hash || result.checkpoint.hmac_seal || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Forensic Chain Architecture Information */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div className="p-4 rounded-xl bg-white border border-[#95A1D8]/20 shadow-xs">
          <div className="flex items-center gap-2 font-bold text-[#132E4F] mb-1">
            <Lock className="w-4 h-4 text-[#275992]" /> 1. Sequential Chaining
          </div>
          <p className="text-[#586D85]">
            Each event hash incorporates the cryptographic hash of the preceding event, preventing deletion or reordering.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-white border border-[#95A1D8]/20 shadow-xs">
          <div className="flex items-center gap-2 font-bold text-[#132E4F] mb-1">
            <Key className="w-4 h-4 text-[#275992]" /> 2. HMAC Sealing
          </div>
          <p className="text-[#586D85]">
            When an attack run concludes, the final state is signed using a server-side HMAC secret key and sealed.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-white border border-[#95A1D8]/20 shadow-xs">
          <div className="flex items-center gap-2 font-bold text-[#132E4F] mb-1">
            <Link2 className="w-4 h-4 text-[#275992]" /> 3. Separation of Duties
          </div>
          <p className="text-[#586D85]">
            Auditors can verify hash chains and inspect governance maps without possessing execution or modification rights.
          </p>
        </div>
      </div>
    </div>
  );
};
