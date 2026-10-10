import React, { useState, useEffect } from 'react';
import { fetchScenarios } from '../api/client';
import { BookOpen, ShieldAlert, CheckCircle, Tag, Info } from 'lucide-react';

interface ScenarioDefinition {
  id: string;
  name: string;
  objective: string;
  preconditions: string[];
  permitted_environment: string;
  expected_boundary: string;
  pass_fail_rule: string;
  framework_mapping: Record<string, string>;
  version: string;
  owner: string;
}

export const Scenarios: React.FC = () => {
  const [scenarios, setScenarios] = useState<ScenarioDefinition[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchScenarios()
      .then(setScenarios)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#275992]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[#132E4F]">Scenario Catalogue</h2>
          <p className="text-[#586D85] mt-1">Authorized test scenarios with predefined acceptance criteria.</p>
        </div>
        <div className="bg-[#E8EEF8] px-4 py-2 rounded-lg text-sm font-medium text-[#275992]">
          Total Scenarios: {scenarios.length}
        </div>
      </div>

      <div className="grid gap-6">
        {scenarios.map((s) => (
          <div key={s.id} className="bg-white rounded-xl shadow-sm border border-[#95A1D8]/20 overflow-hidden">
            <div className="border-b border-[#95A1D8]/20 bg-[#F8FAFD] px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-[#275992] text-white text-xs font-bold px-2 py-1 rounded">
                  {s.id}
                </div>
                <h3 className="font-bold text-[#132E4F]">{s.name}</h3>
                <span className="text-xs text-[#586D85] ml-2">v{s.version}</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-medium text-[#586D85]">
                <Tag className="w-3 h-3" />
                {s.owner}
              </div>
            </div>
            
            <div className="p-6 grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <h4 className="text-xs font-bold text-[#586D85] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5" /> Objective
                  </h4>
                  <p className="text-sm text-[#132E4F]">{s.objective}</p>
                </div>
                
                <div>
                  <h4 className="text-xs font-bold text-[#586D85] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5" /> Preconditions
                  </h4>
                  <ul className="list-disc list-inside text-sm text-[#132E4F] space-y-1">
                    {s.preconditions.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="bg-[#F5EEDB]/30 rounded-lg p-4 border border-[#F5EEDB]">
                  <h4 className="text-xs font-bold text-[#586D85] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <CheckCircle className="w-3.5 h-3.5 text-[#528A74]" /> Acceptance Rule
                  </h4>
                  <p className="text-sm text-[#132E4F]">{s.pass_fail_rule}</p>
                </div>

                <div className="flex flex-col gap-2">
                  <h4 className="text-xs font-bold text-[#586D85] uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5" /> Expected Boundary
                  </h4>
                  <div className="inline-block px-3 py-1 bg-[#E8EEF8] text-[#275992] text-xs font-semibold rounded-full self-start">
                    {s.expected_boundary}
                  </div>
                </div>

                {Object.keys(s.framework_mapping).length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-[#586D85] uppercase tracking-wider mb-2">Framework Mapping</h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(s.framework_mapping).map(([fw, val]) => (
                        <div key={fw} className="text-xs bg-white border border-[#95A1D8]/40 px-2 py-1 rounded text-[#586D85]">
                          <span className="font-semibold text-[#132E4F]">{fw}:</span> {val}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
