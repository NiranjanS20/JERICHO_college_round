import React, { useState, useEffect } from 'react';
import { fetchValidationExperiments, createValidationExperiment } from '../api/client';
import { Beaker, Plus, Activity } from 'lucide-react';

export const Validation: React.FC = () => {
  const [experiments, setExperiments] = useState<any>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadExperiments();
  }, []);

  const loadExperiments = async () => {
    setLoading(true);
    try {
      const data = await fetchValidationExperiments();
      setExperiments(data.experiments || {});
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    const name = prompt('Experiment Name:');
    if (!name) return;
    const variantsStr = prompt('Variants (comma separated):', 'A,B');
    if (!variantsStr) return;
    const variants = variantsStr.split(',').map(v => v.trim());
    await createValidationExperiment({ name, variants });
    loadExperiments();
  };

  return (
    <div className="max-w-[1000px] mx-auto text-textMain font-body">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold font-heading flex items-center gap-2">
          <Beaker className="w-6 h-6 text-brand" /> Validation Experiments
        </h2>
        <button 
          onClick={handleCreate}
          className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded font-medium hover:bg-brand/90 transition"
        >
          <Plus className="w-4 h-4" /> New Experiment
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <div className="w-6 h-6 border-2 border-gray-200 border-t-brand rounded-full animate-spin"></div>
        </div>
      ) : Object.keys(experiments).length === 0 ? (
        <div className="bg-white border border-cardBorder rounded-lg p-12 text-center text-textMuted">
          <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No active validation experiments found.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {Object.entries(experiments).map(([id, exp]: [string, any]) => (
            <div key={id} className="bg-white border border-cardBorder rounded-lg p-6 shadow-sm">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-bold">{exp.name}</h3>
                  <p className="text-xs text-textMuted font-mono mt-1">ID: {id}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                {Object.entries(exp.results || {}).map(([variant, score]: [string, any]) => (
                  <div key={variant} className="bg-gray-50 border border-gray-200 p-3 rounded text-center">
                    <div className="text-xs font-bold text-textMuted uppercase mb-1">Variant {variant}</div>
                    <div className="text-xl font-mono text-brand font-bold">{Number(score).toFixed(2)}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
