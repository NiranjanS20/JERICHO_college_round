import React, { useState } from 'react';
import {
  Shield,
  Crosshair,
  Wrench,
  Search,
  ShieldCheck,
  ArrowRight,
  Lock,
  Sparkles,
  KeyRound,
  CheckCircle2,
  Building,
} from 'lucide-react';
import { WorkspaceRole, ROLE_LABELS, setActiveRole } from '../api/client';

interface SignInProps {
  onSignInSuccess: (role: WorkspaceRole) => void;
  onBackToHome: () => void;
}

const PERSONAS: Array<{
  role: WorkspaceRole;
  name: string;
  email: string;
  dept: string;
  icon: any;
  badgeColor: string;
  bgLight: string;
}> = [
  {
    role: 'safety_lead',
    name: 'Dr. Sarah Chen',
    email: 'safety_lead@acme.ai',
    dept: 'AI Safety & Alignment Group',
    icon: ShieldCheck,
    badgeColor: 'bg-purple-100 text-purple-700 border-purple-200',
    bgLight: 'hover:border-purple-300 hover:bg-purple-50/40',
  },
  {
    role: 'analyst',
    name: 'Alex Rivera',
    email: 'analyst@acme.sec',
    dept: 'Autonomous Red Team Operations',
    icon: Crosshair,
    badgeColor: 'bg-red-100 text-red-700 border-red-200',
    bgLight: 'hover:border-red-300 hover:bg-red-50/40',
  },
  {
    role: 'owner',
    name: 'Marcus Vance',
    email: 'owner@acme.eng',
    dept: 'Core Services & Tool Integrations',
    icon: Wrench,
    badgeColor: 'bg-blue-100 text-blue-700 border-blue-200',
    bgLight: 'hover:border-blue-300 hover:bg-blue-50/40',
  },
  {
    role: 'auditor',
    name: 'Elena Rostova',
    email: 'auditor@compliance.acme',
    dept: 'External Cryptographic Audit & Risk',
    icon: Search,
    badgeColor: 'bg-amber-100 text-amber-700 border-amber-200',
    bgLight: 'hover:border-amber-300 hover:bg-amber-50/40',
  },
];

export const SignIn: React.FC<SignInProps> = ({ onSignInSuccess, onBackToHome }) => {
  const [selectedRole, setSelectedRole] = useState<WorkspaceRole>('safety_lead');
  const [email, setEmail] = useState('safety_lead@acme.ai');
  const [workspace, setWorkspace] = useState('acme-corp-sandbox');
  const [isLoading, setIsLoading] = useState(false);
  const [loginMethod, setLoginMethod] = useState<'persona' | 'sso'>('persona');

  const handleSelectPersona = (p: typeof PERSONAS[0]) => {
    setSelectedRole(p.role);
    setEmail(p.email);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    setTimeout(() => {
      setActiveRole(selectedRole);
      setIsLoading(false);
      onSignInSuccess(selectedRole);
    }, 450);
  };

  const currentPersona = PERSONAS.find(p => p.role === selectedRole) || PERSONAS[0];
  const CurrentIcon = currentPersona.icon;

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-10 px-4 font-body">
      <div className="max-w-4xl w-full grid grid-cols-1 md:grid-cols-12 bg-white rounded-3xl border border-[#95A1D8]/30 shadow-2xl overflow-hidden">
        
        {/* Left Side: Brand & Role Persona Selector */}
        <div className="md:col-span-7 p-8 sm:p-10 border-b md:border-b-0 md:border-r border-[#95A1D8]/20 flex flex-col justify-between bg-gradient-to-br from-white to-[#FFFDF8]">
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="h-10 w-10 rounded-xl bg-[#275992] flex items-center justify-center text-white shadow-md">
                <Shield className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold font-heading text-[#132E4F]">AgentBreak</h1>
                <p className="text-[10px] uppercase font-bold tracking-widest text-[#95A1D8]">
                  ROLE-SCOPED WORKSPACE LOGIN
                </p>
              </div>
            </div>

            <h2 className="text-2xl font-bold text-[#132E4F] tracking-tight mb-2">
              Select Your Operational Persona
            </h2>
            <p className="text-xs text-[#586D85] mb-6 leading-relaxed">
              No passwords required for evaluation. Select your security persona below to access role-scoped telemetry, actions, and evidence boundaries.
            </p>

            {/* Persona Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {PERSONAS.map((p) => {
                const isSelected = selectedRole === p.role;
                const Icon = p.icon;
                return (
                  <button
                    key={p.role}
                    type="button"
                    onClick={() => handleSelectPersona(p)}
                    className={`p-3.5 rounded-2xl border text-left transition-all relative flex flex-col justify-between ${
                      isSelected
                        ? 'border-[#275992] bg-[#275992]/5 shadow-sm ring-2 ring-[#275992]/20'
                        : `border-gray-200 bg-white ${p.bgLight}`
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-2">
                      <div className={`p-1.5 rounded-lg ${p.badgeColor}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase ${p.badgeColor}`}>
                        {ROLE_LABELS[p.role].badge}
                      </span>
                    </div>

                    <div>
                      <div className="text-xs font-bold text-[#132E4F]">{p.name}</div>
                      <div className="text-[11px] font-semibold text-[#275992]">{ROLE_LABELS[p.role].title}</div>
                      <div className="text-[10px] text-[#586D85] truncate mt-0.5">{p.dept}</div>
                    </div>

                    {isSelected && (
                      <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#275992] animate-ping" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-8 pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-[#586D85]">
            <span>Acme Corp Sandbox Verification Suite</span>
            <button
              onClick={onBackToHome}
              className="text-[#275992] font-semibold hover:underline"
            >
              ← Back to Overview
            </button>
          </div>
        </div>

        {/* Right Side: Credential & Sign-in Submission */}
        <div className="md:col-span-5 p-8 sm:p-10 bg-[#FFFAED]/40 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-6">
              <span className="text-xs font-bold uppercase tracking-wider text-[#95A1D8]">Session Scoping</span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${currentPersona.badgeColor}`}>
                {currentPersona.role.toUpperCase()}
              </span>
            </div>

            <div className="mb-6 p-4 rounded-2xl bg-white border border-[#95A1D8]/20 shadow-xs">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-xl ${currentPersona.badgeColor}`}>
                  <CurrentIcon className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[#132E4F]">{currentPersona.name}</div>
                  <div className="text-[11px] font-mono text-[#586D85]">{currentPersona.email}</div>
                </div>
              </div>
              <p className="text-[11px] text-[#586D85] mt-2.5 pt-2 border-t border-gray-100 leading-snug">
                {ROLE_LABELS[selectedRole].desc}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-[#132E4F] mb-1">Authenticated Email</label>
                <div className="relative">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full pl-8 pr-3 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:border-[#275992] bg-white font-mono text-xs"
                  />
                  <KeyRound className="w-4 h-4 text-gray-400 absolute left-2.5 top-3" />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#132E4F] mb-1">Target Workspace Realm</label>
                <div className="relative">
                  <input
                    type="text"
                    value={workspace}
                    onChange={(e) => setWorkspace(e.target.value)}
                    required
                    className="w-full pl-8 pr-3 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:border-[#275992] bg-white font-mono text-xs"
                  />
                  <Building className="w-4 h-4 text-gray-400 absolute left-2.5 top-3" />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-3 px-4 rounded-xl font-semibold text-white bg-[#275992] hover:bg-[#1E4775] transition-all shadow-[0_4px_16px_rgba(39,89,146,0.3)] flex items-center justify-center gap-2 text-xs sm:text-sm disabled:opacity-50"
                >
                  {isLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Authenticating Workspace...</span>
                    </>
                  ) : (
                    <>
                      <span>Enter as {ROLE_LABELS[selectedRole].title}</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          <div className="mt-8 text-[11px] text-[#586D85] text-center bg-white/60 p-3 rounded-xl border border-gray-200/50">
            <Lock className="w-3.5 h-3.5 inline mr-1 text-[#275992]" />
            Enterprise SSO compatible (X-Role header forwarded automatically).
          </div>
        </div>

      </div>
    </div>
  );
};
