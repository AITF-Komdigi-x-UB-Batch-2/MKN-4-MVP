import React from 'react';
import { AlertTriangle } from 'lucide-react';

export interface RecommendationData {
  id: string;
  title: string;
  match: number;
  desc: string;
  reason?: string;
  priority?: 'HIGH' | 'MEDIUM' | 'LOW';
  estimate?: string;
  isReceived: boolean;
}
  
interface RecommendationCardProps {
  data: RecommendationData;
  isSelected?: boolean;
  isLocked?: boolean;
  onToggle?: (id: string, isReceived: boolean) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  data
}) => {
  const normalizedId = data.id === 'PKHT' ? 'PKH Plus' : data.id;

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <h4 className="rec-title">{data.title}</h4>
        {(normalizedId === 'PKH Plus' || normalizedId === 'ASPD') && (
          <span className="match-text">Skor Bantuan: {(data.match / 100).toFixed(3)}</span>
        )}
      </div>

      {data.isReceived && (
        <div className="received-warning">
          <AlertTriangle size={14} />
          Sudah Menerima Program Ini
        </div>
      )}

      <p className="rec-desc">{data.desc}</p>

      {(data.estimate || data.reason) && (
        <div className="rec-estimate">
          {data.estimate ? `Estimasi: ${data.estimate}` : `Alasan: ${data.reason}`}
        </div>
      )}
    </>
  );
};

