import React, { useState, useEffect } from 'react';
import { Users, Shield } from 'lucide-react';

export const Governance: React.FC = () => {
  const [owners, setOwners] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/governance/owners')
      .then(r => r.json())
      .then(data => setOwners(data))
      .catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-xl bg-cardBg border border-cardBorder shadow-sm">
        <h2 className="text-xl font-heading font-bold text-textMain flex items-center gap-2 mb-2">
          <Users className="w-5 h-5 text-[#275992]" /> 
          Component Owner Registry
        </h2>
        <p className="text-sm text-textMain/70 mb-6">
          Accountability mapping for all active components.
        </p>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {owners.map((o, i) => (
             <div key={i} className="p-4 bg-appBg rounded-lg border border-cardBorder flex flex-col justify-between">
               <span className="font-mono text-xs text-textMain/60 mb-2">{o.component}</span>
               <span className="font-semibold text-textMain text-sm flex items-center gap-2">
                 <Shield className="w-4 h-4 text-[#818cf8]" /> {o.owner}
               </span>
             </div>
          ))}
        </div>
      </div>
    </div>
  );
};
