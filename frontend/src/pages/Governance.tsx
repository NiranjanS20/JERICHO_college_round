import React, { useState, useEffect } from 'react';
import { Users, Shield, Edit3, Check, X, ShieldAlert, Sparkles, UserCheck } from 'lucide-react';
import { fetchGovernanceOwners, updateGovernanceOwner, getActiveRole, WorkspaceRole } from '../api/client';

export const Governance: React.FC = () => {
  const [owners, setOwners] = useState<Array<{ component: string; owner: string }>>([]);
  const [editingComponent, setEditingComponent] = useState<string | null>(null);
  const [newOwnerValue, setNewOwnerValue] = useState<string>('');
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [activeRole, setActiveRoleState] = useState<WorkspaceRole>(getActiveRole());

  useEffect(() => {
    loadOwners();
    const handleRoleChanged = (e: any) => {
      setActiveRoleState(e.detail || getActiveRole());
    };
    window.addEventListener('agentbreak_role_changed', handleRoleChanged);
    return () => window.removeEventListener('agentbreak_role_changed', handleRoleChanged);
  }, []);

  const loadOwners = async () => {
    try {
      const data = await fetchGovernanceOwners();
      setOwners(data);
    } catch (e: any) {
      console.error('Failed to load governance owners:', e);
    }
  };

  const startEdit = (component: string, currentOwner: string) => {
    setEditingComponent(component);
    setNewOwnerValue(currentOwner);
    setStatusMsg(null);
  };

  const saveEdit = async (component: string) => {
    try {
      await updateGovernanceOwner(component, newOwnerValue);
      setOwners(prev => prev.map(o => o.component === component ? { ...o, owner: newOwnerValue } : o));
      setEditingComponent(null);
      setStatusMsg({ type: 'success', text: `Assigned component '${component}' to owner '${newOwnerValue}'.` });
      setTimeout(() => setStatusMsg(null), 4000);
    } catch (e: any) {
      setStatusMsg({ type: 'error', text: e.message || 'Failed to update component owner.' });
    }
  };

  const isSafetyLead = activeRole === 'safety_lead';

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="p-6 rounded-2xl bg-white border border-[#95A1D8]/20 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-2">
          <div>
            <h2 className="text-xl font-heading font-bold text-[#132E4F] flex items-center gap-2">
              <Users className="w-6 h-6 text-[#275992]" /> 
              Component Governance & Ownership Registry
            </h2>
            <p className="text-sm text-[#586D85] mt-1">
              Accountability mapping: Every vulnerability finding routes to its accountable engineering owner.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {isSafetyLead ? (
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-purple-100 text-purple-700 border border-purple-200 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" /> Safety Lead (Admin Edit Access)
              </span>
            ) : (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-[#586D85] border border-gray-200 flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5" /> Read-Only View ({activeRole.toUpperCase()})
              </span>
            )}
          </div>
        </div>

        {statusMsg && (
          <div className={`mt-4 p-3 rounded-xl text-xs font-medium flex items-center gap-2 ${
            statusMsg.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'
          }`}>
            {statusMsg.type === 'success' ? <UserCheck className="w-4 h-4 text-emerald-600" /> : <ShieldAlert className="w-4 h-4 text-rose-600" />}
            <span>{statusMsg.text}</span>
          </div>
        )}
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mt-6">
          {owners.map((o, i) => {
            const isEditing = editingComponent === o.component;
            return (
              <div 
                key={i} 
                className="p-5 bg-[#FFFDF8] rounded-xl border border-[#95A1D8]/30 flex flex-col justify-between hover:border-[#275992]/40 transition-all shadow-xs"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-gray-100 text-[#132E4F]">
                      {o.component}
                    </span>
                    <span className="text-[10px] uppercase font-semibold text-[#586D85]">
                      Component
                    </span>
                  </div>

                  {isEditing ? (
                    <div className="mt-3 flex items-center gap-2">
                      <input
                        value={newOwnerValue}
                        onChange={e => setNewOwnerValue(e.target.value)}
                        className="px-2.5 py-1 text-xs rounded-lg border border-[#275992] bg-white flex-1 font-semibold text-[#132E4F] focus:outline-none"
                        placeholder="Owner name / team..."
                        autoFocus
                      />
                      <button
                        onClick={() => saveEdit(o.component)}
                        className="p-1.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                        title="Save owner"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setEditingComponent(null)}
                        className="p-1.5 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                        title="Cancel"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <div className="mt-2 flex items-center justify-between">
                      <span className="font-semibold text-[#132E4F] text-sm flex items-center gap-2">
                        <Shield className="w-4 h-4 text-[#275992]" /> {o.owner}
                      </span>

                      {isSafetyLead && (
                        <button
                          onClick={() => startEdit(o.component, o.owner)}
                          className="p-1.5 rounded-lg text-[#586D85] hover:text-[#275992] hover:bg-[#95A1D8]/20 transition-all text-xs flex items-center gap-1 font-semibold"
                          title="Reassign owner"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                          <span>Reassign</span>
                        </button>
                      )}
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-gray-100 text-[11px] text-[#586D85] flex items-center justify-between">
                  <span>Policy Enforced: Active</span>
                  <span className="text-emerald-600 font-semibold font-mono">Bound</span>
                </div>
              </div>
            );
          })}
        </div>

        {owners.length === 0 && (
          <div className="p-8 text-center text-sm text-[#586D85]">
            No governance mappings found.
          </div>
        )}
      </div>

      <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-200/60 text-xs text-purple-900 leading-relaxed flex items-start gap-3">
        <Sparkles className="w-4 h-4 text-purple-600 flex-shrink-0 mt-0.5" />
        <div>
          <strong className="font-semibold">Separation of Duties Architecture:</strong> Only the{' '}
          <span className="font-bold">Safety Lead</span> can alter ownership allocations. Red Team Analysts, Component Owners, and Auditors are restricted from reassigning components to preserve organizational boundaries.
        </div>
      </div>
    </div>
  );
};
