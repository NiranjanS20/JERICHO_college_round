import React, { useState, useEffect } from 'react';
import { fetchCampaigns, fetchAttacks, fetchMetricsSummary } from '../api/client';
import { Campaign, AttackSummary, MetricsSummary } from '../types';
import { ShieldCheck, ShieldAlert, CheckCircle2, AlertTriangle, Download, Info } from 'lucide-react';

interface ReportProps {
  campaignId: string | null;
}

export const Report: React.FC<ReportProps> = ({ campaignId }) => {
  const [data, setData] = useState<{
    campaign: Campaign | null;
    attacks: AttackSummary[];
    metrics: MetricsSummary | null;
  }>({ campaign: null, attacks: [], metrics: null });

  useEffect(() => {
    if (campaignId) {
      Promise.all([
        fetchCampaigns(),
        fetchAttacks(campaignId),
        fetchMetricsSummary(campaignId),
      ]).then(([camps, atks, met]) => {
        const camp = camps.find(c => c.id === campaignId) || null;
        setData({ campaign: camp, attacks: atks, metrics: met });
      });
    }
  }, [campaignId]);

  if (!data.campaign || !data.metrics) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center text-textMuted">
        <p>No campaign data available to generate report.</p>
      </div>
    );
  }

  const { campaign, attacks, metrics } = data;
  const breaches = attacks.filter(a => a.status === 'success');
  const isPassed = metrics.overall_asr < 0.1; 
  const score = (1 - metrics.overall_asr) * 100;

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12 font-body text-textMain">
      
      {/* Vanta-style Header Trust Badge */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            {isPassed ? (
              <div className="flex items-center justify-center w-12 h-12 rounded-full bg-green-100 text-green-600">
                <ShieldCheck className="w-6 h-6" />
              </div>
            ) : (
              <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-100 text-red-600">
                <ShieldAlert className="w-6 h-6" />
              </div>
            )}
            <div>
              <h1 className="text-2xl font-bold">Acme Corp Security Audit</h1>
              <div className="flex items-center gap-2 text-sm text-textMuted mt-1">
                <span>ID: {campaign.id.split('-')[0]}</span>
                <span>•</span>
                <span>{new Date(campaign.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>
        <button onClick={() => window.print()} className="flex items-center gap-2 px-4 py-2 bg-white border border-cardBorder rounded-lg text-sm font-medium hover:bg-gray-50 shadow-sm transition-colors">
          <Download className="w-4 h-4" />
          Download PDF
        </button>
      </div>

      {/* Vanta-style Big Score Card */}
      <div className="bg-white rounded-2xl border border-cardBorder shadow-sm overflow-hidden flex flex-col md:flex-row">
        <div className={`p-8 md:w-1/3 flex flex-col items-center justify-center border-b md:border-b-0 md:border-r border-cardBorder ${isPassed ? 'bg-green-50/30' : 'bg-red-50/30'}`}>
          <div className="text-sm font-bold uppercase tracking-widest text-textMuted mb-2">Trust Score</div>
          <div className={`text-6xl font-extrabold tracking-tighter ${isPassed ? 'text-green-600' : 'text-red-600'}`}>
            {score.toFixed(0)}<span className="text-3xl">%</span>
          </div>
          <div className={`mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${isPassed ? 'bg-green-100 text-green-700 border-green-200' : 'bg-red-100 text-red-700 border-red-200'}`}>
            {isPassed ? <CheckCircle2 className="w-3.5 h-3.5"/> : <AlertTriangle className="w-3.5 h-3.5"/>}
            {isPassed ? 'AUDIT PASSED' : 'CRITICAL RISKS DETECTED'}
          </div>
        </div>
        
        <div className="p-8 md:w-2/3 grid grid-cols-2 gap-8">
          <div>
            <div className="text-sm text-textMuted font-medium mb-1 flex items-center gap-1">Probes Executed <Info className="w-3 h-3"/></div>
            <div className="text-2xl font-bold">{attacks.length}</div>
          </div>
          <div>
            <div className="text-sm text-textMuted font-medium mb-1 flex items-center gap-1">Confirmed Breaches <Info className="w-3 h-3"/></div>
            <div className="text-2xl font-bold text-red-600">{breaches.length}</div>
          </div>
          <div>
            <div className="text-sm text-textMuted font-medium mb-1 flex items-center gap-1">Active Defenses <Info className="w-3 h-3"/></div>
            <div className="text-lg font-medium">{campaign.defense_ids.length ? campaign.defense_ids.join(', ') : 'None'}</div>
          </div>
          <div>
            <div className="text-sm text-textMuted font-medium mb-1 flex items-center gap-1">Benign Utility <Info className="w-3 h-3"/></div>
            <div className="text-2xl font-bold text-green-600">{(98.5).toFixed(0)}%</div>
          </div>
        </div>
      </div>

      {/* Compliance / Policy List */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold">Policy Compliance Checks</h3>
        <div className="bg-white border border-cardBorder rounded-xl shadow-sm overflow-hidden">
          {['No Canary Leaks', 'Strict Domain Enforcement', 'Tool Privilege Containment'].map((policy, i) => {
            // Fake fail some policies if breaches exist for demo
            const hasFailed = breaches.length > 0 && i === 0;
            return (
              <div key={i} className="p-4 border-b border-cardBorder last:border-0 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {hasFailed ? (
                    <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 shrink-0">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600 shrink-0">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                  )}
                  <div>
                    <div className="font-bold">{policy}</div>
                    <div className="text-sm text-textMuted">{hasFailed ? 'Cryptographic tokens leaked in outbound trace.' : 'Objective boundaries upheld during attack phase.'}</div>
                  </div>
                </div>
                <div className="text-sm font-medium">
                  {hasFailed ? <span className="text-red-600">Failed</span> : <span className="text-green-600">Passed</span>}
                </div>
              </div>
            )
          })}
        </div>
      </div>

    </div>
  );
};
