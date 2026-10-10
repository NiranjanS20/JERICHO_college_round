import React, { useState, useEffect } from 'react';
import { fetchPendingApprovals, approveAction, rejectAction } from '../api/client';
import { CheckCircle, XCircle, ShieldAlert } from 'lucide-react';

export const Approvals: React.FC = () => {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const data = await fetchPendingApprovals();
      setApprovals(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    try {
      if (action === 'approve') await approveAction(id);
      else await rejectAction(id);
      loadApprovals();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="max-w-[1000px] mx-auto text-textMain font-body">
      <div className="mb-6">
        <h2 className="text-2xl font-bold font-heading flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-brand" /> Human-in-the-Loop Approvals
        </h2>
        <p className="text-sm text-textMuted mt-1">Review and approve high-risk agent actions.</p>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <div className="w-6 h-6 border-2 border-gray-200 border-t-brand rounded-full animate-spin"></div>
        </div>
      ) : approvals.length === 0 ? (
        <div className="bg-white border border-cardBorder rounded-lg p-12 text-center text-textMuted">
          <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500 opacity-50" />
          <p>No pending approvals. Inbox zero!</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {approvals.map((app) => (
            <div key={app.id} className="bg-white border border-cardBorder rounded-lg p-6 shadow-sm flex items-center justify-between">
              <div>
                <h3 className="font-bold text-lg">{app.action_type || 'Unknown Action'}</h3>
                <p className="text-sm text-textMuted mt-1">Requested by: {app.requester || 'System'}</p>
                <div className="mt-2 text-xs font-mono bg-gray-50 border border-gray-200 p-2 rounded inline-block">
                  {JSON.stringify(app.payload || {})}
                </div>
              </div>
              <div className="flex gap-2">
                <button 
                  onClick={() => handleAction(app.id, 'reject')}
                  className="p-2 text-red-600 hover:bg-red-50 rounded border border-transparent hover:border-red-200 transition"
                  title="Reject"
                >
                  <XCircle className="w-6 h-6" />
                </button>
                <button 
                  onClick={() => handleAction(app.id, 'approve')}
                  className="p-2 text-green-600 hover:bg-green-50 rounded border border-transparent hover:border-green-200 transition"
                  title="Approve"
                >
                  <CheckCircle className="w-6 h-6" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
