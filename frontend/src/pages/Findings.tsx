import React, { useState, useEffect } from 'react';
import { fetchAttack, replayAttack } from '../api/client';
import { AttackSummary } from '../types';
import { Search, Filter, ShieldAlert, Zap, Activity, Terminal, Play, CheckCircle } from 'lucide-react';

interface FindingsProps {
  attacks: AttackSummary[];
}

export const Findings: React.FC<FindingsProps> = ({ attacks }) => {
  const [selectedAttack, setSelectedAttack] = useState<string | null>(null);
  const [attackDetail, setAttackDetail] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isReplaying, setIsReplaying] = useState(false);
  const [replayResult, setReplayResult] = useState<any>(null);

  useEffect(() => {
    if (selectedAttack) {
      setIsLoading(true);
      fetchAttack(selectedAttack).then(data => {
        setAttackDetail(data);
        setIsLoading(false);
        setReplayResult(null);
      });
    }
  }, [selectedAttack]);

  const handleReplay = async () => {
    if (!selectedAttack) return;
    setIsReplaying(true);
    try {
      const res = await replayAttack(selectedAttack, 5, []);
      setReplayResult(res);
    } catch (e) {
      console.error('Replay failed', e);
    } finally {
      setIsReplaying(false);
    }
  };

  const getStatusColor = (status: string) => status === 'success' ? 'text-red-600 bg-red-50 border-red-200' : 'text-green-600 bg-green-50 border-green-200';

  return (
    <div className="max-w-[1400px] mx-auto h-[85vh] flex gap-6 text-textMain font-body selection:bg-gray-200">
      
      {/* Sentry-style Event List (Left Panel) */}
      <div className="w-1/3 flex flex-col bg-white border border-cardBorder rounded-lg overflow-hidden shadow-sm">
        
        {/* Header / Filter */}
        <div className="p-3 border-b border-cardBorder bg-gray-50/50">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-cardBorder rounded-md focus-within:border-gray-400 transition-colors shadow-sm">
            <Search className="w-4 h-4 text-textMuted" />
            <input type="text" placeholder="Search events, policies, tags..." className="bg-transparent border-none outline-none text-xs w-full text-textMain placeholder-gray-400 font-mono" />
          </div>
          <div className="flex gap-2 mt-3 px-1">
            <button className="text-[10px] uppercase font-bold text-textMuted hover:text-textMain flex items-center gap-1"><Filter className="w-3 h-3"/> ALL ({attacks.length})</button>
            <button className="text-[10px] uppercase font-bold text-red-500 hover:text-red-600 flex items-center gap-1">BREACHES</button>
          </div>
        </div>

        {/* Dense Event List */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {attacks.map((atk) => {
            const isSelected = selectedAttack === atk.id;
            return (
              <div 
                key={atk.id} 
                onClick={() => setSelectedAttack(atk.id)}
                className={`p-3 border-b border-gray-100 cursor-pointer transition-all ${isSelected ? 'bg-blue-50/50 border-l-2 border-l-blue-500' : 'hover:bg-gray-50 border-l-2 border-l-transparent'}`}
              >
                <div className="flex justify-between items-start mb-1.5">
                  <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${getStatusColor(atk.status)}`}>
                    {atk.status === 'success' ? 'BREACH' : 'BLOCK'}
                  </span>
                  <span className="text-[10px] font-mono text-gray-400">{atk.id.split('-')[0]}</span>
                </div>
                <div className="text-sm font-medium text-textMain leading-tight mb-2 line-clamp-2">{atk.goal}</div>
                <div className="flex gap-2 text-[10px] font-mono">
                  <span className="text-textMuted bg-gray-100 px-1 rounded border border-gray-200">{atk.category}</span>
                  <span className="text-textMuted bg-gray-100 px-1 rounded border border-gray-200 truncate">{atk.strategy}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Langfuse-style Trace Detail (Right Panel) */}
      <div className="w-2/3 flex flex-col bg-white border border-cardBorder rounded-lg overflow-hidden shadow-sm">
        {!selectedAttack ? (
          <div className="flex-1 flex flex-col items-center justify-center text-textMuted">
            <Activity className="w-8 h-8 mb-3 opacity-50" />
            <p className="text-sm font-medium">Select an event to view trace details</p>
          </div>
        ) : isLoading || !attackDetail ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="w-5 h-5 border-2 border-gray-200 border-t-textMain rounded-full animate-spin"></div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            
            {/* Header Details */}
            <div className="p-6 border-b border-cardBorder bg-gray-50/30">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-bold mb-2">{attackDetail.goal}</h2>
                  <div className="flex gap-3 text-xs font-mono text-textMuted">
                    <span className="flex items-center gap-1 bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200"><Terminal className="w-3 h-3"/> {attackDetail.id}</span>
                    <span className="bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200">Score: {attackDetail.partial_score.toFixed(2)}</span>
                  </div>
                </div>
                <button 
                  onClick={handleReplay} 
                  disabled={isReplaying}
                  className="px-3 py-1.5 bg-white border border-cardBorder text-textMain font-medium text-xs rounded shadow-sm hover:bg-gray-50 disabled:opacity-50 flex items-center gap-2"
                >
                  <Play className="w-3 h-3" /> {isReplaying ? 'Running...' : 'Replay (N=5)'}
                </button>
              </div>

              {/* Oracle Verdict block */}
              {attackDetail.oracle_verdict && (
                <div className={`p-4 rounded border mt-4 ${attackDetail.status === 'success' ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                  <div className="text-xs font-bold uppercase mb-2 flex items-center gap-2">
                    {attackDetail.status === 'success' ? <ShieldAlert className="w-4 h-4 text-red-500"/> : <CheckCircle className="w-4 h-4 text-green-500"/>}
                    <span className={attackDetail.status === 'success' ? 'text-red-600' : 'text-green-600'}>Oracle Verdict: {attackDetail.status.toUpperCase()}</span>
                  </div>
                  <div className="text-sm font-mono text-textMain/80">
                    Policy Violated: <span className="text-textMain font-bold bg-white px-1 rounded border border-gray-200">{attackDetail.oracle_verdict.violated_policies?.join(', ') || 'None'}</span>
                  </div>
                </div>
              )}

              {/* Replay block */}
              {replayResult && (
                <div className="mt-4 grid grid-cols-3 gap-4">
                  <div className="bg-white p-3 rounded border border-cardBorder shadow-sm">
                    <div className="text-[10px] text-textMuted font-bold uppercase mb-1">Empirical ASR</div>
                    <div className="text-xl font-mono text-textMain">{(replayResult.success_rate * 100).toFixed(1)}%</div>
                  </div>
                  <div className="bg-white p-3 rounded border border-cardBorder shadow-sm">
                    <div className="text-[10px] text-textMuted font-bold uppercase mb-1">Wilson 95% CI</div>
                    <div className="text-xl font-mono text-textMain">[{replayResult.wilson_ci_low.toFixed(2)}, {replayResult.wilson_ci_high.toFixed(2)}]</div>
                  </div>
                  <div className="bg-white p-3 rounded border border-cardBorder shadow-sm">
                    <div className="text-[10px] text-textMuted font-bold uppercase mb-1">Passes</div>
                    <div className="text-xl font-mono text-textMain">{replayResult.successes}/{replayResult.n_runs}</div>
                  </div>
                </div>
              )}
            </div>

            {/* Trace Steps Timeline */}
            <div className="p-6 bg-appBg/50">
              <h3 className="text-sm font-bold uppercase tracking-wider text-textMuted mb-6">Execution Trace</h3>
              <div className="space-y-6">
                {attackDetail.trace_steps?.map((step: any, idx: number) => (
                  <div key={step.id} className="relative pl-6 border-l border-gray-300">
                    <div className="absolute left-[-5px] top-1 w-2 h-2 rounded-full bg-gray-400 border border-white"></div>
                    <div className="flex gap-2 items-center mb-2">
                      <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded ${
                        step.role === 'user' ? 'bg-blue-50 text-blue-600 border border-blue-200' : 
                        step.role === 'assistant' ? 'bg-purple-50 text-purple-600 border border-purple-200' : 
                        'bg-yellow-50 text-yellow-600 border border-yellow-200'
                      }`}>
                        {step.role.toUpperCase()} {step.tool_name ? `(${step.tool_name})` : ''}
                      </span>
                      <span className="text-[10px] font-mono text-gray-400">STEP {step.step_index}</span>
                    </div>
                    
                    <div className="bg-white border border-cardBorder shadow-sm rounded-md p-3 text-xs font-mono text-textMain whitespace-pre-wrap leading-relaxed overflow-x-auto">
                      {step.content}
                    </div>
                    {step.tool_args && (
                      <div className="mt-2 bg-gray-50 border border-gray-200 rounded-md p-3 text-[10px] font-mono text-textMuted overflow-x-auto">
                        <span className="text-gray-400 font-bold select-none">ARGS </span>
                        {JSON.stringify(step.tool_args, null, 2)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}
      </div>

    </div>
  );
};
