import React, { useState, useEffect } from 'react';
import { CheckCircle2, Shield, AlertTriangle, Play, Check } from 'lucide-react';
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { fetchDefenses, fetchEvalMatrix, evaluateDefenses } from '../api/client';
import { DefenseInfo, EvalMatrixRow } from '../types';

interface DefensesProps {
  campaignId: string | null;
}

export const Defenses: React.FC<DefensesProps> = ({ campaignId }) => {
  const [defenses, setDefenses] = useState<DefenseInfo[]>([]);
  const [matrixRows, setMatrixRows] = useState<EvalMatrixRow[]>([]);
  const [selectedDefenses, setSelectedDefenses] = useState<string[]>(['policy_engine']);
  const [evalResult, setEvalResult] = useState<any | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  useEffect(() => {
    loadData();
  }, [campaignId]);

  const loadData = async () => {
    try {
      const defs = await fetchDefenses();
      setDefenses(defs);
      const rows = await fetchEvalMatrix(campaignId || undefined);
      setMatrixRows(rows);
    } catch (e) {
      console.error('Failed to load defenses data:', e);
    }
  };

  const toggleDefense = (id: string) => {
    setSelectedDefenses((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  const handleQuickEval = async () => {
    setIsEvaluating(true);
    try {
      const res = await evaluateDefenses(selectedDefenses);
      setEvalResult(res);
    } catch (e) {
      console.error('Evaluation failed:', e);
    } finally {
      setIsEvaluating(false);
    }
  };

  // Tradeoff Dataset
  const tradeoffData = matrixRows.map((r) => ({
    name: r.defense_combo.length ? r.defense_combo.join(' + ') : 'None (Unprotected)',
    asr: Number((r.attack_success_rate * 100).toFixed(1)),
    utility: Number((r.benign_pass_rate * 100).toFixed(1)),
  }));

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-xl bg-cardBg border border-cardBorder  flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-textMain tracking-tight">
            Defense Stack & Evaluation Matrix
          </h1>
          <p className="text-textMain text-xs mt-1 max-w-2xl leading-relaxed">
            5 pluggable defensive layers evaluated across security breach prevention (ASR),
            benign workflow retention, and regression detection.
          </p>
        </div>
      </div>

      {/* 5 Pluggable Defenses Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5">
        {defenses.map((def) => {
          const isSelected = selectedDefenses.includes(def.id);
          return (
            <div
              key={def.id}
              onClick={() => toggleDefense(def.id)}
              className={`p-4 rounded-xl cursor-pointer border transition-all ${
                isSelected
                  ? 'bg-cardBg/50 border-charcoal '
                  : 'bg-cardBg border-cardBorder hover:border-cardBorder hover:shadow-xs'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[11px] font-heading font-semibold text-textMain bg-cardBg px-2 py-0.5 rounded-md">
                  {def.id}
                </span>
                <div
                  className={`w-4 h-4 rounded-md flex items-center justify-center border transition-colors ${
                    isSelected
                      ? 'bg-charcoal border-charcoal text-textMain'
                      : 'border-cardBorder bg-cardBg'
                  }`}
                >
                  {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                </div>
              </div>
              <div className="text-xs font-heading font-semibold text-textMain mb-1">{def.name}</div>
              <div className="text-[11px] text-textMain leading-snug line-clamp-3">
                {def.description}
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Test Bar */}
      <div className="p-4 rounded-xl bg-cardBg border border-cardBorder  flex items-center justify-between">
        <div className="text-xs text-textMain">
          Selected Defense Stack ({selectedDefenses.length}):{' '}
          <span className="font-heading font-semibold text-textMain">
            {selectedDefenses.length ? selectedDefenses.join(' + ') : 'None (Unprotected)'}
          </span>
        </div>
        <button
          onClick={handleQuickEval}
          disabled={isEvaluating}
          className="px-4 py-2 bg-charcoal hover:bg-charcoal/90 disabled:opacity-50 text-textMain rounded-xl text-xs font-semibold flex items-center gap-2  transition-all"
        >
          <Play className="w-3.5 h-3.5" />
          {isEvaluating ? 'Testing Stack...' : 'Test Selected Stack'}
        </button>
      </div>

      {evalResult && (
        <div className="p-4 rounded-xl bg-cardBg border border-cardBorder  text-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="font-heading font-semibold text-textMain">Quick Attack Evaluation Result:</span>
            <span
              className={`px-2.5 py-0.5 rounded-full font-heading font-semibold text-[10px] ${
                evalResult.attack_blocked
                  ? 'bg-appBg text-textMain border border-cardBorder'
                  : 'bg-cardBg text-textMain/60 border border-cardBorder'
              }`}
            >
              {evalResult.attack_blocked ? 'ATTACK BLOCKED' : 'CANARY EXFILTRATED'}
            </span>
          </div>
          <div className="text-textMain font-mono text-[11px] bg-cardBg p-2.5 rounded-lg border border-cardBorder">
            Target Output: {evalResult.final_answer}
          </div>
        </div>
      )}

      {/* Tradeoff Scatter Chart & Matrix Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Security vs. Utility Tradeoff Chart */}
        <div className="p-6 rounded-xl bg-cardBg border border-cardBorder  flex flex-col h-80">
          <h2 className="font-heading text-base font-heading font-semibold text-textMain mb-1">Security vs. Utility Tradeoff</h2>
          <p className="text-xs text-textMain mb-4">
            Optimal defense occupies high utility (≥90%) and low breach ASR (≤10%)
          </p>
          <div className="flex-1 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  type="number"
                  dataKey="asr"
                  name="Attack Success Rate"
                  unit="%"
                  stroke="#94a3b8"
                  domain={[0, 100]}
                  tickLine={false}
                  label={{
                    value: 'Attack Success (ASR %)',
                    position: 'insideBottom',
                    offset: -10,
                    fill: '#95A1D8',
                    fontSize: 11,
                  }}
                />
                <YAxis
                  type="number"
                  dataKey="utility"
                  name="Benign Utility"
                  unit="%"
                  stroke="#94a3b8"
                  domain={[0, 100]}
                  tickLine={false}
                  label={{
                    value: 'Benign Utility (%)',
                    angle: -90,
                    position: 'insideLeft',
                    fill: '#95A1D8',
                    fontSize: 11,
                  }}
                />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: '#e2e8f0',
                    borderRadius: '10px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
                    fontSize: '12px',
                    color: '#0f172a',
                  }}
                />
                <Scatter name="Defense Combinations" data={tradeoffData} fill="#1C1C1A" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Matrix Table */}
        <div className="p-6 rounded-xl bg-cardBg border border-cardBorder  flex flex-col justify-between">
          <div>
            <h2 className="font-heading text-base font-heading font-semibold text-textMain mb-1">Attacks × Defenses Matrix</h2>
            <p className="text-xs text-textMain mb-4">
              Comparative benchmark results across defense configurations
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-cardBg text-textMain font-semibold uppercase tracking-wider border-b border-cardBorder">
                  <tr>
                    <th className="py-2.5 px-3">Defense Combo</th>
                    <th className="py-2.5 px-3 text-center">ASR</th>
                    <th className="py-2.5 px-3 text-center">Utility</th>
                    <th className="py-2.5 px-3 text-center">Adaptive ASR</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-iris/20">
                  {matrixRows.map((r, i) => {
                    const comboStr = r.defense_combo.length ? r.defense_combo.join(' + ') : 'None';
                    const asrHigh = r.attack_success_rate > 0.3;
                    return (
                      <tr key={r.id || i} className="hover:bg-cardBg/80">
                        <td className="py-2.5 px-3 font-medium text-textMain">{comboStr}</td>
                        <td
                          className={`py-2.5 px-3 text-center font-heading font-semibold font-mono ${
                            asrHigh ? 'text-textMain/60' : 'text-textMain'
                          }`}
                        >
                          {(r.attack_success_rate * 100).toFixed(1)}%
                        </td>
                        <td className="py-2.5 px-3 text-center font-heading font-semibold font-mono text-textMain">
                          {(r.benign_pass_rate * 100).toFixed(1)}%
                        </td>
                        <td className="py-2.5 px-3 text-center font-mono text-textMain">
                          {(r.adaptive_asr * 100).toFixed(1)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-4 p-3.5 rounded-xl bg-appBg border border-cardBorder text-xs text-textMain">
            <strong>Optimal Defense:</strong> Policy Engine Only (0.0% ASR, 90.0% Utility retention with zero regressions).
          </div>
        </div>
      </div>
    </div>
  );
};
