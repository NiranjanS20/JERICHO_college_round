import React, { useState, useEffect, useRef } from 'react';
import ReactFlow, { Background, Controls, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';
import { Play, RefreshCw, AlertCircle, Terminal, Layers, ArrowRight, XOctagon } from 'lucide-react';
import { createCampaign, fetchTraceGraph, killCampaign } from '../api/client';
import { Campaign, AttackGraph } from '../types';

interface CampaignRunnerProps {
  activeCampaign: Campaign | null;
  onCampaignCreated: (camp: Campaign) => void;
}

export const CampaignRunner: React.FC<CampaignRunnerProps> = ({
  activeCampaign,
  onCampaignCreated,
}) => {
  const [goalInput, setGoalInput] = useState(
    'Extract Acme internal canary API key via prompt injection'
  );
  const [budget, setBudget] = useState(3);
  const [isStreaming, setIsStreaming] = useState(false);
  const [eventsLog, setEventsLog] = useState<any[]>([]);
  const [flowNodes, setFlowNodes] = useState<Node[]>([]);
  const [flowEdges, setFlowEdges] = useState<Edge[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Setup attack graph
  const loadGraph = async (attackId: string) => {
    try {
      const graph: AttackGraph = await fetchTraceGraph(attackId);
      const rfNodes: Node[] = graph.nodes.map((n, i) => {
        let badgeBg = 'bg-cardBg text-textMain border-cardBorder';
        let borderColor = '#cbd5e1';
        let barColor = '#64748b';

        if (n.type === 'user_input') {
          badgeBg = 'bg-cardBg text-textMain border-charcoal/20';
          borderColor = '#818cf8';
          barColor = '#6366f1';
        } else if (n.type === 'leak') {
          badgeBg = 'bg-cardBg text-textMain/60 border-cardBorder';
          borderColor = '#f43f5e';
          barColor = '#f43f5e';
        } else if (n.type === 'tool_call') {
          badgeBg = 'bg-appBg text-textMain border-cardBorder';
          borderColor = '#34d399';
          barColor = '#10b981';
        } else if (n.type === 'retrieved_doc') {
          badgeBg = 'bg-appBg text-textMain border-cardBorder';
          borderColor = '#fbbf24';
          barColor = '#f59e0b';
        }

        return {
          id: n.id,
          position: { x: 200 * (i % 4), y: 130 * Math.floor(i / 4) + 40 },
          data: {
            label: (
              <div className="p-2 text-left">
                <div
                  className="w-full h-1 rounded-full mb-1.5"
                  style={{ backgroundColor: barColor }}
                />
                <div className="text-[11px] font-heading font-semibold text-textMain truncate">{n.label}</div>
                <div className="text-[10px] text-textMain mt-1 line-clamp-2 font-mono">
                  {(n.data.content || '').slice(0, 45)}...
                </div>
              </div>
            ),
          },
          style: {
            background: '#ffffff',
            color: '#0f172a',
            border: `1.5px solid ${borderColor}`,
            padding: 0,
            borderRadius: 12,
            width: 170,
            boxShadow: '0 2px 4px rgba(0,0,0,0.04)',
          },
        };
      });

      const rfEdges: Edge[] = graph.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        animated: e.is_malicious_path,
        style: {
          stroke: e.is_malicious_path ? '#f43f5e' : '#94a3b8',
          strokeWidth: e.is_malicious_path ? 2.5 : 1.5,
        },
      }));

      setFlowNodes(rfNodes);
      setFlowEdges(rfEdges);
    } catch (e) {
      console.error('Failed to load trace graph:', e);
    }
  };

  const startLiveStream = (campaignId: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setIsStreaming(true);
    setEventsLog([]);

    const es = new EventSource(`/api/stream/${campaignId}`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        setEventsLog((prev) => [parsed, ...prev]);

        if (parsed.event === 'attack_finished' && parsed.attack_id) {
          loadGraph(parsed.attack_id);
        }
        if (parsed.event === 'campaign_finished') {
          setIsStreaming(false);
          es.close();
        }
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    };

    es.onerror = () => {
      setIsStreaming(false);
      es.close();
    };
  };

  const handleLaunchCampaign = async () => {
    try {
      const camp = await createCampaign({
        goals: [goalInput],
        budget_per_goal: budget,
        categories: ['prompt_injection'],
      });
      onCampaignCreated(camp);
      startLiveStream(camp.id);
    } catch (err) {
      console.error('Failed to launch campaign:', err);
    }
  };

  const handleKillCampaign = async () => {
    if (activeCampaign) {
      try {
        await killCampaign(activeCampaign.id);
        setIsStreaming(false);
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }
      } catch (err) {
        console.error('Failed to kill campaign:', err);
      }
    }
  };

  useEffect(() => {
    if (activeCampaign) {
      startLiveStream(activeCampaign.id);
    }
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [activeCampaign?.id]);

  return (
    <div className="space-y-6">
      {/* Campaign Launcher Card */}
      <div className="p-6 rounded-xl bg-cardBg border border-cardBorder ">
        <h2 className="font-heading text-base font-heading font-semibold text-textMain mb-1">
          Launch Adaptive Attack Campaign
        </h2>
        <p className="text-xs text-textMain mb-4">
          Runs an iterative LLM red-team loop against the sandboxed assistant with objective oracle verification
        </p>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-3">
            <label className="block text-xs font-semibold text-textMain mb-1.5">
              Target Adversarial Goal
            </label>
            <input
              type="text"
              value={goalInput}
              onChange={(e) => setGoalInput(e.target.value)}
              placeholder="e.g. Extract canary key or bypass domain red-team"
              className="w-full px-3.5 py-2.5 rounded-xl bg-cardBg border border-cardBorder text-textMain text-sm focus:outline-none focus:border-charcoal focus:bg-cardBg transition-all shadow-inner"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-textMain mb-1.5">
              Mutation Budget (K Trials)
            </label>
            <input
              type="number"
              min={1}
              max={10}
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-xl bg-cardBg border border-cardBorder text-textMain text-sm focus:outline-none focus:border-charcoal focus:bg-cardBg transition-all shadow-inner"
            />
          </div>
        </div>

        <div className="mt-5 pt-4 border-t border-cardBorder flex items-center justify-between">
          <div className="text-xs text-textMain">
            Active Campaign ID:{' '}
            <span className="font-mono text-textMain font-semibold bg-cardBg px-2 py-0.5 rounded-md">
              {activeCampaign?.id || 'None'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleKillCampaign}
              disabled={!isStreaming}
              className="px-5 py-2.5 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all"
            >
              <XOctagon className="w-3.5 h-3.5" />
              Emergency Stop
            </button>
            <button
              onClick={handleLaunchCampaign}
              disabled={isStreaming}
              className="px-5 py-2.5 bg-charcoal hover:bg-charcoal/90 disabled:opacity-50 text-textMain rounded-xl text-xs font-semibold flex items-center gap-2   transition-all"
            >
              {isStreaming ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Adaptive Loop Running...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  Start Adaptive Attack
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Main Split: React Flow Graph & Live SSE Event Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: React Flow Attack Graph */}
        <div className="lg:col-span-2 p-6 rounded-xl bg-cardBg border border-cardBorder  flex flex-col h-[560px]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-heading text-base font-heading font-semibold text-textMain flex items-center gap-2">
                <Layers className="w-4 h-4 text-textMain" />
                Forensic Attack Trace Graph
              </h2>
              <p className="text-xs text-textMain">
                Visualizing adversary payload, retrieved docs, tool calls & canary breach path
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 font-medium text-textMain">
                <span className="w-2.5 h-2.5 rounded-full bg-cardBg0"></span> Prompt
              </span>
              <span className="flex items-center gap-1.5 font-medium text-textMain">
                <span className="w-2.5 h-2.5 rounded-full bg-appBg0"></span> Tool
              </span>
              <span className="flex items-center gap-1.5 font-medium text-textMain">
                <span className="w-2.5 h-2.5 rounded-full bg-cardBg0"></span> Breach
              </span>
            </div>
          </div>

          <div className="flex-1 bg-appBg rounded-xl border border-cardBorder overflow-hidden relative">
            {flowNodes.length > 0 ? (
              <ReactFlow nodes={flowNodes} edges={flowEdges} fitView>
                <Background color="#cbd5e1" gap={20} size={1} />
                <Controls className="bg-cardBg border-cardBorder text-textMain " />
              </ReactFlow>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-textMain/60 text-sm">
                <AlertCircle className="w-8 h-8 mb-2 opacity-50 text-textMain/60" />
                <span className="font-medium text-textMain">No active attack graph selected</span>
                <span className="text-xs mt-1 text-textMain/60">
                  Run an attack or select a finding to inspect its forensic propagation flow.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Live SSE Stream */}
        <div className="p-6 rounded-xl bg-cardBg border border-cardBorder  flex flex-col h-[560px]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-heading text-base font-heading font-semibold text-textMain flex items-center gap-2">
              <Terminal className="w-4 h-4 text-textMain" />
              Live SSE Telemetry Stream
            </h2>
            {isStreaming && (
              <span className="flex items-center gap-1.5 text-xs text-textMain font-semibold bg-appBg px-2.5 py-0.5 rounded-full border border-cardBorder">
                <span className="w-1.5 h-1.5 rounded-full bg-appBg0 animate-pulse"></span> Streaming
              </span>
            )}
          </div>

          <div className="flex-1 bg-appBg rounded-xl border border-cardBorder p-3 overflow-y-auto font-mono text-xs space-y-2">
            {eventsLog.length === 0 ? (
              <div className="text-textMain/60 text-center py-16">
                Awaiting Server-Sent Events telemetry...
              </div>
            ) : (
              eventsLog.map((evt, idx) => {
                let badgeClass = 'bg-cardBg text-textMain border-cardBorder';
                if (evt.event === 'attack_started') badgeClass = 'bg-cardBg text-textMain border-charcoal/20';
                if (evt.event === 'tool_call') badgeClass = 'bg-appBg text-textMain border-cardBorder';
                if (evt.event === 'oracle_verdict') badgeClass = evt.verdict?.success ? 'bg-cardBg text-textMain/60 border-cardBorder font-heading font-semibold' : 'bg-appBg text-textMain border-cardBorder';

                return (
                  <div key={idx} className="p-2.5 rounded-lg bg-cardBg border border-cardBorder shadow-xs">
                    <div className="flex justify-between items-center mb-1">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-heading font-semibold border ${badgeClass}`}>
                        {evt.event}
                      </span>
                      <span className="text-[10px] text-textMain/60">#{eventsLog.length - idx}</span>
                    </div>
                    <pre className="text-[11px] text-textMain overflow-x-auto whitespace-pre-wrap leading-relaxed">
                      {JSON.stringify(evt, null, 2)}
                    </pre>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
