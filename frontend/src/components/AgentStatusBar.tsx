import type { AgentHealth } from "../types";

interface AgentBarProps {
  agents: AgentHealth[];
}

export const AgentStatusBar: React.FC<AgentBarProps> = ({ agents }) => {
  return (
    <div className="w-full bg-slate-950/90 border-t border-slate-800/80 px-4 py-2 flex flex-wrap items-center justify-between text-xs backdrop-blur-lg">
      <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-slate-400 text-[11px]">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span>Multi-Agent Mesh:</span>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {agents.length === 0 ? (
          <span className="text-slate-500 italic">Initializing micro-agents...</span>
        ) : (
          agents.map((agent) => {
            const isHealthy = agent.status === "healthy" || agent.status === "processing";
            return (
              <div
                key={agent.agent_id}
                className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-2 py-1 rounded-md"
                title={`Processed: ${agent.processed_count} | Errors: ${agent.error_count} | Latency: ${agent.average_latency_ms}ms`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    isHealthy ? "bg-emerald-400" : "bg-rose-500"
                  }`}
                />
                <span className="text-slate-200 font-semibold text-[11px] truncate max-w-[110px]">
                  {agent.role_name.split(" ")[0]}
                </span>
                <span className="text-slate-500 text-[10px] font-mono">
                  {agent.average_latency_ms > 0 ? `${agent.average_latency_ms.toFixed(1)}ms` : "idle"}
                </span>
              </div>
            );
          })
        )}
      </div>

      <div className="text-[11px] text-slate-500 font-medium hidden md:block">
        Microsoft Premier League Hackathon Engine
      </div>
    </div>
  );
};
