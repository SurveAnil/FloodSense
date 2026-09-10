import { CloudRain, Eye, Gauge, Wind } from 'lucide-react';
import type { DashboardData } from '../types/domain';

export function RainfallStrip({ rainfall }: { rainfall: DashboardData['rainfall'] }) {
  return (
    <section className="rainfall-strip" aria-labelledby="rainfall-title">
      <div className="section-kicker" id="rainfall-title"><CloudRain size={16} /> Rainfall context <span className="observed-label">Observed + forecast</span></div>
      <div className="rainfall-grid">
        <div className="rainfall-item"><Eye size={18} /><div><span>Current observed</span><strong>{rainfall.current}</strong></div></div>
        <div className="rainfall-item"><Gauge size={18} /><div><span>Forecast predicted</span><strong>{rainfall.forecast}</strong></div></div>
        <div className="rainfall-item"><Wind size={18} /><div><span>Nowcast</span><strong>{rainfall.nowcast}</strong></div></div>
        <div className="rainfall-outlook">{rainfall.outlook}</div>
      </div>
    </section>
  );
}
