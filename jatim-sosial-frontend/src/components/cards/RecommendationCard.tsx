import React from 'react';
import { ShieldCheck, Home, Briefcase, AlertTriangle, Check } from 'lucide-react';

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
  data,
  isSelected = false,
  isLocked = false,
  onToggle
}) => {
  const getIcon = (id: string) => {
    switch (id) {
      case 'pkh': return <Briefcase size={20} className="text-blue" />;
      case 'rutilahu': return <Home size={20} className="text-orange" />;
      default: return <ShieldCheck size={20} className="text-cyan" />;
    }
  };

  const isHighMatch = data.match >= 80;
  const cardStyle: React.CSSProperties = isHighMatch ? {
    background: 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)',
    border: isSelected ? '2px solid #d97706' : '1px solid #fcd34d',
    boxShadow: '0 4px 6px -1px rgba(234, 179, 8, 0.1)',
    cursor: isLocked ? 'default' : 'pointer',
    borderRadius: '12px',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    transition: 'all 0.2s',
    position: 'relative'
  } : {
    background: '#ffffff',
    border: isSelected ? '2px solid #2563eb' : '1px solid #e2e8f0',
    cursor: isLocked ? 'default' : 'pointer',
    borderRadius: '12px',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    transition: 'all 0.2s',
    position: 'relative'
  };

  return (
    <div
      className={`rec-card ${isSelected ? 'selected' : ''} ${isLocked ? 'locked' : ''}`}
      style={cardStyle}
      onClick={() => onToggle && onToggle(data.id, data.isReceived)}
    >
      {/* Checkbox Area */}
      <div className="rec-checkbox">
        {isSelected ? <Check size={16} className="text-white" /> : null}
      </div>

      <div className="rec-card-header flex-between">
        <div className="rec-icon">
          {getIcon(data.id)}
        </div>
        {data.priority && (
          <span className={`priority-badge ${data.priority.toLowerCase()}`}>
            {data.priority}
          </span>
        )}
      </div>

      <div className="flex-between mb-2">
        <h4 className="rec-title">{data.title}</h4>
        <span className="match-text">Skor Bantuan: {(data.match / 100).toFixed(3)}</span>
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
    </div>
  );
};

