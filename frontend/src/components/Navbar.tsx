import React from 'react';
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
  UserCheck
} from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  onLoadDemo: () => void;
  isLoadingDemo: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onTabChange,
  onLoadDemo,
  isLoadingDemo,
}) => {
  const tabs = [
    { id: 'home', label: 'Front Page', icon: Sparkles },
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'runner', label: 'Campaign Runner', icon: Crosshair },
    { id: 'findings', label: 'Findings', icon: ShieldAlert },
    { id: 'defenses', label: 'Defenses', icon: CheckCircle2 },
    { id: 'validation', label: 'Validation', icon: Beaker },
    { id: 'approvals', label: 'Approvals', icon: UserCheck },
    { id: 'report', label: 'Report', icon: FileText },
  ];

  return (
    <header className="border-b border-[#95A1D8]/20 bg-[#FFFAED]/85 backdrop-blur-md sticky top-0 z-50 shadow-[0_4px_20px_rgba(149,161,216,0.12)]">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        
        <div
          className="flex items-center space-x-3 cursor-pointer select-none group"
          onClick={() => onTabChange('home')}
        >
          <div className="h-9 w-9 rounded-xl bg-[#275992] flex items-center justify-center text-[#FFFAED] transition-transform group-hover:bg-[#1E4775]">
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

        <nav className="flex items-center space-x-1">
          {tabs.map((tab) => {
            const active = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex items-center space-x-1.5 px-4 py-2 rounded-full text-sm font-semibold transition-all ${
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

        <div className="flex items-center space-x-3">
          <button
            onClick={onLoadDemo}
            disabled={isLoadingDemo}
            className="flex items-center space-x-2 px-4 py-2 rounded-full text-xs font-semibold bg-[#FFFDF8] border border-[#95A1D8]/30 text-[#275992] hover:bg-[#F5EEDB] transition-colors disabled:opacity-50 shadow-sm"
          >
            <span className="inline-block w-2 h-2 rounded-full bg-[#528A74] animate-pulse"></span>
            <span>{isLoadingDemo ? 'Loading...' : 'Demo Data'}</span>
          </button>

          <button
            onClick={() => onTabChange('runner')}
            className="flex items-center space-x-1 px-5 py-2 rounded-full text-xs sm:text-sm font-semibold bg-[#275992] text-[#FFFAED] hover:bg-[#1E4775] transition-all shadow-[0_4px_16px_rgba(39,89,146,0.3)]"
          >
            <span>Launch Campaign</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
};
