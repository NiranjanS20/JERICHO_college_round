import React, { useState } from 'react';
import {
  ShieldAlert,
  BarChart3,
  Crosshair,
  FileText,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  Shield,
  Beaker,
  UserCheck,
  ListTree,
  Archive,
  Users,
  ShieldCheck,
  ChevronDown,
  Octagon,
  Eye,
  Lock,
  Wrench,
  Search
} from 'lucide-react';
import { WorkspaceRole, ROLE_LABELS } from '../api/client';

interface NavbarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  onLoadDemo: () => void;
  isLoadingDemo: boolean;
  activeRole: WorkspaceRole;
  onRoleChange: (role: WorkspaceRole) => void;
  onEmergencyStop?: () => void;
}

const ROLE_ICONS: Record<WorkspaceRole, React.ComponentType<{ className?: string }>> = {
  analyst: Crosshair,
  owner: Wrench,
  auditor: Search,
  safety_lead: ShieldCheck,
};

const ROLE_COLORS: Record<WorkspaceRole, { badgeBg: string; text: string; dot: string }> = {
  analyst: { badgeBg: 'bg-red-500/10 border-red-500/30', text: 'text-red-700', dot: 'bg-red-500' },
  owner: { badgeBg: 'bg-blue-500/10 border-blue-500/30', text: 'text-blue-700', dot: 'bg-blue-500' },
  auditor: { badgeBg: 'bg-amber-500/10 border-amber-500/30', text: 'text-amber-700', dot: 'bg-amber-500' },
  safety_lead: { badgeBg: 'bg-purple-500/10 border-purple-500/30', text: 'text-purple-700', dot: 'bg-purple-600' },
};

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onTabChange,
  onLoadDemo,
  isLoadingDemo,
  activeRole,
  onRoleChange,
  onEmergencyStop,
}) => {
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);

  // Tab definitions with role accessibility
  const allTabs = [
    { id: 'home', label: 'Front Page', icon: Sparkles, roles: ['analyst', 'owner', 'auditor', 'safety_lead'] },
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3, roles: ['analyst', 'owner', 'auditor', 'safety_lead'] },
    { id: 'runner', label: 'Campaign Runner', icon: Crosshair, roles: ['analyst', 'safety_lead'] },
    { id: 'validation', label: 'Experiments', icon: Beaker, roles: ['analyst', 'owner', 'auditor', 'safety_lead'] },
    { id: 'findings', label: 'Findings', icon: ShieldAlert, roles: ['analyst', 'owner', 'auditor', 'safety_lead'] },
    { id: 'scenarios', label: 'Scenarios', icon: ListTree, roles: ['analyst', 'safety_lead'] },
    { id: 'integrity', label: 'Integrity', icon: ShieldCheck, roles: ['auditor', 'safety_lead'] },
    { id: 'governance', label: 'Governance', icon: Users, roles: ['owner', 'auditor', 'safety_lead'] },
    { id: 'defenses', label: 'Defenses', icon: CheckCircle2, roles: ['analyst', 'safety_lead'] },
    { id: 'approvals', label: 'Approvals', icon: UserCheck, roles: ['safety_lead'] },
    { id: 'report', label: 'Report', icon: FileText, roles: ['analyst', 'owner', 'auditor', 'safety_lead'] },
  ];

  const visibleTabs = allTabs.filter(t => t.roles.includes(activeRole));
  const ActiveRoleIcon = ROLE_ICONS[activeRole] || Shield;
  const activeRoleColor = ROLE_COLORS[activeRole];

  return (
    <header className="border-b border-[#95A1D8]/20 bg-[#FFFAED]/90 backdrop-blur-md sticky top-0 z-50 shadow-[0_4px_20px_rgba(149,161,216,0.12)]">
      <div className="max-w-[1500px] mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between gap-4">
        
        {/* Brand & Platform Badge */}
        <div
          className="flex items-center space-x-3 cursor-pointer select-none group flex-shrink-0"
          onClick={() => onTabChange('home')}
        >
          <div className="h-9 w-9 rounded-xl bg-[#275992] flex items-center justify-center text-[#FFFAED] transition-transform group-hover:bg-[#1E4775] shadow-sm">
            <Shield className="w-5 h-5 text-[#FFFAED]" />
          </div>
          <div className="flex flex-col">
            <div className="text-xl font-bold tracking-tight text-[#132E4F] flex items-center gap-2 group-hover:text-[#275992] transition-colors">
              AgentBreak
            </div>
            <div className="text-[10px] uppercase text-[#95A1D8] font-bold tracking-[0.2em] -mt-1">
              AUTONOMOUS RED TEAM
            </div>
          </div>
        </div>

        {/* Dynamic Navigation Tabs */}
        <nav className="flex items-center space-x-1 overflow-x-auto scrollbar-none py-1">
          {visibleTabs.map((tab) => {
            const active = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs sm:text-sm font-semibold transition-all whitespace-nowrap ${
                  active
                    ? 'bg-[#275992] text-[#FFFAED] shadow-[0_4px_12px_rgba(39,89,146,0.25)]'
                    : 'text-[#132E4F]/75 hover:text-[#275992] hover:bg-[#95A1D8]/15'
                }`}
              >
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Workspace Role Switcher & Controls */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          
          {/* Role Switcher Dropdown */}
          <div className="relative">
            <button
              onClick={() => setRoleMenuOpen(!roleMenuOpen)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all shadow-sm ${activeRoleColor.badgeBg} ${activeRoleColor.text}`}
              title="Switch role-scoped workspace (Evaluation view & action scoping)"
            >
              <span className={`w-2 h-2 rounded-full ${activeRoleColor.dot}`}></span>
              <ActiveRoleIcon className="w-3.5 h-3.5" />
              <span className="font-bold">{ROLE_LABELS[activeRole].title}</span>
              <ChevronDown className="w-3.5 h-3.5 opacity-60" />
            </button>

            {roleMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setRoleMenuOpen(false)}
                />
                <div className="absolute right-0 mt-2 w-72 rounded-2xl bg-white border border-[#95A1D8]/30 shadow-2xl z-50 p-2 overflow-hidden animate-in fade-in-50 zoom-in-95 duration-100">
                  <div className="px-3 py-2 border-b border-[#95A1D8]/15 mb-1">
                    <div className="text-[11px] font-bold uppercase tracking-wider text-[#95A1D8]">
                      Role-Scoped Workspace
                    </div>
                    <div className="text-[11px] text-[#586D85] mt-0.5">
                      No-login header switcher (SSO pluggable)
                    </div>
                  </div>

                  {(['safety_lead', 'analyst', 'owner', 'auditor'] as WorkspaceRole[]).map((r) => {
                    const isSelected = activeRole === r;
                    const meta = ROLE_LABELS[r];
                    const Icon = ROLE_ICONS[r];
                    const color = ROLE_COLORS[r];

                    return (
                      <button
                        key={r}
                        onClick={() => {
                          onRoleChange(r);
                          setRoleMenuOpen(false);
                        }}
                        className={`w-full text-left p-2.5 rounded-xl transition-all flex items-start gap-3 ${
                          isSelected
                            ? 'bg-[#275992]/10 border border-[#275992]/20'
                            : 'hover:bg-gray-50 border border-transparent'
                        }`}
                      >
                        <div className={`mt-0.5 p-1.5 rounded-lg ${color.badgeBg}`}>
                          <Icon className={`w-4 h-4 ${color.text}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-[#132E4F]">
                              {meta.title}
                            </span>
                            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${color.badgeBg} ${color.text}`}>
                              {meta.badge}
                            </span>
                          </div>
                          <p className="text-[11px] text-[#586D85] mt-0.5 leading-snug line-clamp-2">
                            {meta.desc}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          {/* Demo Data button */}
          <button
            onClick={onLoadDemo}
            disabled={isLoadingDemo}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-[#FFFDF8] border border-[#95A1D8]/30 text-[#275992] hover:bg-[#F5EEDB] transition-colors disabled:opacity-50 shadow-sm"
          >
            <span className="inline-block w-2 h-2 rounded-full bg-[#528A74] animate-pulse"></span>
            <span>{isLoadingDemo ? 'Loading...' : 'Demo'}</span>
          </button>

          {/* Launch Campaign or Emergency Stop depending on Role */}
          {(activeRole === 'analyst' || activeRole === 'safety_lead') && (
            <button
              onClick={() => onTabChange('runner')}
              className="flex items-center space-x-1 px-4 py-1.5 rounded-full text-xs font-semibold bg-[#275992] text-[#FFFAED] hover:bg-[#1E4775] transition-all shadow-[0_4px_16px_rgba(39,89,146,0.3)]"
            >
              <span>Launch</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}

          {activeRole === 'auditor' && (
            <button
              onClick={() => onTabChange('integrity')}
              className="flex items-center space-x-1 px-4 py-1.5 rounded-full text-xs font-semibold bg-[#B58900] text-white hover:bg-[#967000] transition-all shadow-sm"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Audit Integrity</span>
            </button>
          )}

          {activeRole === 'owner' && (
            <button
              onClick={() => onTabChange('findings')}
              className="flex items-center space-x-1 px-4 py-1.5 rounded-full text-xs font-semibold bg-[#2A6F97] text-white hover:bg-[#014F86] transition-all shadow-sm"
            >
              <Wrench className="w-3.5 h-3.5" />
              <span>Review Findings</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
