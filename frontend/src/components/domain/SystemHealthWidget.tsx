import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../../api/health';
import { Panel } from '../ui/Panel';
import { ArrowRight, XCircle } from 'lucide-react';

export const SystemHealthWidget: React.FC = () => {
  const { data: health, isError } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: healthApi.getHealthStatus,
    refetchInterval: 10000,
  });

  const isHealthy = !isError && health?.status === 'healthy';

  const services = [
    { name: 'Evidence Processing', status: isHealthy ? 'OPERATIONAL' : 'DEGRADED' },
    { name: 'Intelligence Engine (C3)', status: isHealthy ? 'OPERATIONAL' : 'DEGRADED' },
    { name: 'Graph Projection (Neo4j)', status: isHealthy ? 'OPERATIONAL' : 'DEGRADED' },
  ];

  return (
    <Panel
      title="SYSTEM HEALTH"
      headerAction={
        <button className="text-xs font-semibold text-blue-700 hover:text-blue-900 flex items-center space-x-1">
          <span>View System Status</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      }
      className="h-full"
    >
      <div className="space-y-2.5">
        {services.map((s) => (
          <div key={s.name} className="flex items-center justify-between py-1.5 px-2 bg-slate-50 rounded border border-slate-200">
            <span className="text-xs font-semibold text-slate-800">{s.name}</span>
            <div className="flex items-center space-x-1.5">
              {s.status === 'OPERATIONAL' ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
                  <span className="text-[10px] font-mono font-bold text-emerald-800 uppercase tracking-wider">
                    OPERATIONAL
                  </span>
                </>
              ) : (
                <>
                  <XCircle className="w-3.5 h-3.5 text-red-600" />
                  <span className="text-[10px] font-mono font-bold text-red-800 uppercase tracking-wider">
                    DEGRADED
                  </span>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
};
