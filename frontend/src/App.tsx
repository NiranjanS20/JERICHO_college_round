import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LandingPage } from './pages/LandingPage';
import { SignIn } from './pages/SignIn';
import { Dashboard } from './pages/Dashboard';
import { CampaignRunner } from './pages/CampaignRunner';
import { Findings } from './pages/Findings';
import { Defenses } from './pages/Defenses';
import { Report } from './pages/Report';
import { Validation } from './pages/Validation';
import { Approvals } from './pages/Approvals';
import { Scenarios } from './pages/Scenarios';
import { Integrity } from './pages/Integrity';
import { Governance } from './pages/Governance';
import {
  fetchCampaigns,
  fetchAttacks,
  fetchMetricsSummary,
  loadDemoCampaign,
  getActiveRole,
  setActiveRole,
  WorkspaceRole,
} from './api/client';
import { Campaign, AttackSummary, MetricsSummary } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('home');
  const [activeRole, setActiveRoleState] = useState<WorkspaceRole>(getActiveRole());
  const [integrityRunId, setIntegrityRunId] = useState<string>('');
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [activeCampaign, setActiveCampaign] = useState<Campaign | null>(null);
  const [attacks, setAttacks] = useState<AttackSummary[]>([]);
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [isLoadingDemo, setIsLoadingDemo] = useState(false);

  useEffect(() => {
    refreshAllData();
  }, []);

  const refreshAllData = async () => {
    try {
      const campList = await fetchCampaigns();
      setCampaigns(campList);

      const latestCamp = campList[0] || null;
      setActiveCampaign(latestCamp);

      const atkList = await fetchAttacks(latestCamp?.id);
      setAttacks(atkList);

      const m = await fetchMetricsSummary(latestCamp?.id);
      setMetrics(m);
    } catch (e) {
      console.error('Failed to load initial data:', e);
    }
  };

  const handleRoleChange = (newRole: WorkspaceRole) => {
    setActiveRole(newRole);
    setActiveRoleState(newRole);

    // Permission checks for active tab:
    if (newRole === 'analyst') {
      if (['integrity', 'governance', 'approvals'].includes(currentTab)) {
        setCurrentTab('dashboard');
      }
    } else if (newRole === 'owner') {
      if (['runner', 'scenarios', 'integrity', 'defenses', 'approvals'].includes(currentTab)) {
        setCurrentTab('dashboard');
      }
    } else if (newRole === 'auditor') {
      if (['runner', 'scenarios', 'defenses', 'approvals'].includes(currentTab)) {
        setCurrentTab('integrity');
      }
    }
  };

  const handleNavigateToIntegrity = (runId: string) => {
    setIntegrityRunId(runId);
    if (activeRole !== 'auditor' && activeRole !== 'safety_lead') {
      handleRoleChange('auditor');
    }
    setCurrentTab('integrity');
  };

  const handleLoadDemo = async () => {
    setIsLoadingDemo(true);
    try {
      await loadDemoCampaign();
      await refreshAllData();
      setCurrentTab('dashboard');
    } catch (e) {
      console.error('Failed to load demo:', e);
    } finally {
      setIsLoadingDemo(false);
    }
  };

  const handleCampaignCreated = (newCamp: Campaign) => {
    setCampaigns((prev) => [newCamp, ...prev]);
    setActiveCampaign(newCamp);
    refreshAllData();
  };

  return (
    <div className="min-h-screen bg-[#FFFAED] flex flex-col font-body text-[#132E4F] selection:bg-[#275992] selection:text-[#FFFAED]">
      {currentTab !== 'home' && currentTab !== 'signin' && (
        <Navbar
          currentTab={currentTab}
          onTabChange={setCurrentTab}
          onLoadDemo={handleLoadDemo}
          isLoadingDemo={isLoadingDemo}
          activeRole={activeRole}
          onRoleChange={handleRoleChange}
        />
      )}

      {currentTab === 'home' ? (
        <LandingPage
          onEnterApp={(tab) => setCurrentTab(tab || 'dashboard')}
          onLoadDemo={handleLoadDemo}
          isLoadingDemo={isLoadingDemo}
        />
      ) : currentTab === 'signin' ? (
        <SignIn
          onSignInSuccess={(role) => {
            handleRoleChange(role);
            setCurrentTab('dashboard');
          }}
          onBackToHome={() => setCurrentTab('home')}
        />
      ) : (
        <main className="flex-1 max-w-[1500px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {currentTab === 'dashboard' && (
            <Dashboard
              metrics={metrics}
              attacks={attacks}
              campaign={activeCampaign}
              activeRole={activeRole}
              onNavigate={(page) => setCurrentTab(page)}
              onNavigateToIntegrity={handleNavigateToIntegrity}
              onLoadDemo={handleLoadDemo}
            />
          )}
          {currentTab === 'scenarios' && <Scenarios />}
          {currentTab === 'integrity' && <Integrity initialRunId={integrityRunId} />}
          {currentTab === 'governance' && <Governance />}
          {currentTab === 'runner' && (
            <CampaignRunner
              activeCampaign={activeCampaign}
              onCampaignCreated={handleCampaignCreated}
              onNavigateToIntegrity={handleNavigateToIntegrity}
              onNavigate={(page) => setCurrentTab(page)}
            />
          )}
          {currentTab === 'findings' && (
            <Findings
              attacks={attacks}
              onNavigateToIntegrity={handleNavigateToIntegrity}
            />
          )}
          {currentTab === 'defenses' && <Defenses campaignId={activeCampaign?.id || null} />}
          {currentTab === 'validation' && <Validation />}
          {currentTab === 'approvals' && <Approvals />}
          {currentTab === 'report' && (
            <Report
              campaignId={activeCampaign?.id || null}
              onNavigateToIntegrity={handleNavigateToIntegrity}
            />
          )}
        </main>
      )}

      {currentTab !== 'home' && (
        <footer className="border-t border-[#95A1D8]/20 bg-[#F5EEDB]/60 py-8 text-center text-xs text-[#586D85] font-medium">
          <div className="max-w-[1500px] mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-md bg-[#275992] flex items-center justify-center text-white">
                <span className="text-[10px] font-bold">A</span>
              </div>
              <strong className="text-[#132E4F]">AgentBreak</strong> • Autonomous Red-Team Telemetry Suite
            </div>
            <div className="text-[#586D85]">
              Acme Corp Defensive Security Research • Objective Sandboxed Verification
            </div>
          </div>
        </footer>
      )}
    </div>
  );
};

export default App;
