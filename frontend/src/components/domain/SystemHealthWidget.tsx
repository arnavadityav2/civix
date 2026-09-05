import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../../api/health';
import { Panel } from '../ui/Panel';
import { ArrowRight, XCircle, CheckCircle2 } from 'lucide-react';

export const SystemHealthWidget: React.FC = () => {
  const { data: health, isError } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: healthApi.getHealthStatus,
    refetchInterval: 10000,
  });

  const isHealthy = !isError && health?.status === 'healthy';

  const services = [
    { name: 'Evidence Processing', id: 'evidence', status: isHealthy ? 'OPERATIONAL' : 'DEGRADED' },
    { name: 'Intelligence Engine (C3)', id: 'c3', status: isHealthy ? 'OPERATIONAL' : 'DEGRADED' },
    { name: 'Graph Projection (Neo4j)', id: 'neo4j', status: isHealthy ? 'OPERATIONAL' : 'DEGRADED' },
  ];

  return (
    <Panel
      title="SYSTEM HEALTH"
      accent={isHealthy ? 'green' : 'red'}
      headerAction={
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5">
            <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-civix-green animate-pulse' : 'bg-civix-red'}`} />
            <span className={`text-[10px] font-mono font-bold uppercase tracking-widest ${isHealthy ? 'text-civix-green' : 'text-civix-red'}`}>
              {isHealthy ? 'ALL SYSTEMS GO' : 'DEGRADED'}
            </span>
          </div>
          <button className="text-[11px] font-semibold text-civix-blue-light hover:text-civix-text-primary flex items-center space-x-1 transition-colors font-mono">
            <span>System Status</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      }
      className="h-full"
    >
      <div className="space-y-2">
        {services.map((s) => (
          <div
            key={s.id}
            className="flex items-center justify-between py-2 px-3 bg-civix-surface-2 rounded-sm border border-civix-border"
          >
            <span className="text-xs font-semibold text-civix-text-secondary">{s.name}</span>
            <div className="flex items-center space-x-1.5">
              {s.status === 'OPERATIONAL' ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-civix-green" />
                  <span className="text-[9px] font-mono font-bold text-civix-green uppercase tracking-widest">
                    OPERATIONAL
                  </span>
                </>
              ) : (
                <>
                  <XCircle className="w-3.5 h-3.5 text-civix-red" />
                  <span className="text-[9px] font-mono font-bold text-civix-red uppercase tracking-widest">
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
