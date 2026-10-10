import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { ArrowUpRight, Activity, Zap, Shield, Play } from 'lucide-react';
import { Campaign, AttackSummary, MetricsSummary } from '../types';

interface DashboardProps {
  metrics: MetricsSummary | null;
  attacks: AttackSummary[];
  campaign: Campaign | null;
  onNavigate: (page: 'dashboard'|'findings'|'matrix'|'defenses'|'runner'|'report') => void;
  onLoadDemo: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ attacks, campaign, onNavigate }) => {
  const totalAttacks = attacks.length;
  const breaches = attacks.filter(a => a.status === 'success').length;
  const asr = totalAttacks > 0 ? (breaches / totalAttacks) * 100 : 0;

  const categoryCounts = attacks.reduce((acc, a) => {
    acc[a.category] = (acc[a.category] || { breached: 0, resisted: 0 });
    if (a.status === 'success') acc[a.category].breached++;
    else acc[a.category].resisted++;
    return acc;
  }, {} as Record<string, { breached: number, resisted: number }>);

  const chartData = Object.entries(categoryCounts).map(([name, counts]) => ({
    name: name.replace('_', ' '),
    breached: counts.breached,
    resisted: counts.resisted,
  }));
  
  return (
    <div className="max-w-7xl mx-auto space-y-6 text-textMain font-body selection:bg-gray-200">
      
      {/* Linear-style Header (Light Mode) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4 pb-4 border-b border-cardBorder">
        <div>
          <h1 className="text-xl font-medium tracking-tight flex items-center gap-2">
            <Activity className="w-5 h-5 text-textMuted" />
            Telemetry Dashboard
          </h1>
          <p className="text-textMuted text-sm mt-1">Real-time attack metrics and sandbox status.</p>
        </div>
        
        <div className="flex gap-2">
          <button onClick={() => onNavigate('report')} className="px-3 py-1.5 rounded-md text-sm font-medium border border-cardBorder hover:bg-gray-50 transition-colors shadow-sm bg-white">
            Export Report
          </button>
          <button onClick={() => onNavigate('runner')} className="flex items-center gap-2 bg-textMain text-white px-4 py-1.5 rounded-md text-sm font-medium hover:bg-black transition-all shadow-premium">
            <Play className="w-3.5 h-3.5" />
            Launch Campaign
          </button>
        </div>
      </div>

      {/* Datadog-style Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Probes', value: totalAttacks, sub: 'Active session', color: 'text-textMain' },
          { label: 'Breaches', value: breaches, sub: 'Cryptographic leaks', color: 'text-red-600' },
          { label: 'Success Rate', value: `${asr.toFixed(1)}%`, sub: 'Overall ASR', color: asr > 30 ? 'text-red-600' : 'text-green-600' },
          { label: 'Target Defenses', value: campaign?.defense_ids?.length || 0, sub: 'Active policies', color: 'text-textMain' },
        ].map((m, i) => (
          <div key={i} className="bg-white border border-cardBorder rounded-lg p-5 shadow-sm">
            <div className="text-xs font-medium text-textMuted uppercase tracking-wider mb-2">{m.label}</div>
            <div className={`text-3xl font-medium ${m.color} mb-1 tracking-tight`}>{m.value}</div>
            <div className="text-xs text-textMuted">{m.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Chart (Datadog/Linear style) */}
        <div className="lg:col-span-2 bg-white border border-cardBorder rounded-lg p-5 flex flex-col shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-sm font-medium">Vector Distribution</h3>
            <div className="flex gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-red-600 font-medium"><span className="w-2 h-2 rounded-full bg-red-500"></span> Breached</span>
              <span className="flex items-center gap-1.5 text-textMuted font-medium"><span className="w-2 h-2 rounded-full bg-gray-300"></span> Resisted</span>
            </div>
          </div>
          
          <div className="flex-1 min-h-[250px]">
             {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
                  <XAxis dataKey="name" stroke="#6B7280" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#6B7280" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip
                    cursor={{ fill: '#F9F9FB' }}
                    contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', borderRadius: '6px', color: '#111827', fontSize: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}
                  />
                  <Bar dataKey="breached" fill="#EF4444" name="Breached" radius={[2, 2, 0, 0]} stackId="a" />
                  <Bar dataKey="resisted" fill="#D1D5DB" name="Resisted" radius={[2, 2, 0, 0]} stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-textMuted text-sm">No telemetry data available.</div>
            )}
          </div>
        </div>

        {/* Langfuse-style Traces List */}
        <div className="lg:col-span-1 bg-white border border-cardBorder rounded-lg flex flex-col overflow-hidden shadow-sm">
          <div className="p-4 border-b border-cardBorder flex justify-between items-center bg-gray-50/50">
            <h3 className="text-sm font-medium flex items-center gap-2">
              <Zap className="w-4 h-4 text-textMuted" /> Live Traces
            </h3>
            <button onClick={() => onNavigate('findings')} className="text-xs text-textMuted hover:text-textMain transition-colors flex items-center">
              View all <ArrowUpRight className="w-3 h-3 ml-0.5" />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {attacks.slice(0, 7).map((atk) => (
              <div key={atk.id} onClick={() => onNavigate('findings')} className="p-3 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer flex justify-between items-start">
                <div className="flex gap-3 overflow-hidden">
                  <div className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${atk.status === 'success' ? 'bg-red-500 shadow-sm' : 'bg-gray-300'}`}></div>
                  <div className="truncate">
                    <div className="text-sm font-medium truncate">{atk.goal}</div>
                    <div className="text-xs text-textMuted mt-0.5 font-mono truncate">{atk.id.split('-')[0]} • {atk.strategy}</div>
                  </div>
                </div>
                <div className={`text-xs font-mono font-medium px-1.5 py-0.5 rounded ${atk.status === 'success' ? 'bg-red-50 text-red-600 border border-red-100' : 'bg-gray-50 text-textMuted border border-gray-200'}`}>
                  {atk.status === 'success' ? 'BREACH' : 'BLOCK'}
                </div>
              </div>
            ))}
            {attacks.length === 0 && (
              <div className="p-6 text-center text-textMuted text-sm">System idle. No traces recorded.</div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
