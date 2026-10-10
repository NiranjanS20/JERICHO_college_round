import React, { useState, useEffect } from 'react';
import { Package, Shield, Wrench, Cpu, Fingerprint } from 'lucide-react';

interface ComponentVersion {
  id: string;
  type: string;
  name: string;
  version: string;
  description: string;
}

export const Inventory: React.FC = () => {
  const [components, setComponents] = useState<ComponentVersion[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch('/api/inventory')
      .then(r => r.json())
      .then(setComponents)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  const typeIcons: Record<string, React.ReactNode> = {
    model: <Cpu className="w-4 h-4" />,
    tool: <Wrench className="w-4 h-4" />,

    defense: <Shield className="w-4 h-4" />,
    dependency: <Package className="w-4 h-4" />
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#275992]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-[#132E4F]">Component Inventory</h2>
        <p className="text-[#586D85] mt-1">Registry of all models, tools, defenses, and dependencies (GOV-02).</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-[#95A1D8]/20 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#F8FAFD] border-b border-[#95A1D8]/20 text-xs uppercase tracking-wider text-[#586D85]">
              <th className="p-4 font-bold">Type</th>
              <th className="p-4 font-bold">Name</th>
              <th className="p-4 font-bold">Version</th>
              <th className="p-4 font-bold">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#95A1D8]/10 text-sm">
            {components.map((c) => (
              <tr key={c.id} className="hover:bg-[#F8FAFD]/50 transition-colors">
                <td className="p-4">
                  <div className="flex items-center gap-2 text-[#275992] font-semibold">
                    {typeIcons[c.type] || <Fingerprint className="w-4 h-4" />}
                    <span className="capitalize">{c.type}</span>
                  </div>
                </td>
                <td className="p-4 font-semibold text-[#132E4F]">{c.name}</td>
                <td className="p-4"><span className="bg-[#E8EEF8] text-[#275992] px-2 py-1 rounded text-xs font-mono">{c.version}</span></td>
                <td className="p-4 text-[#586D85]">{c.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
