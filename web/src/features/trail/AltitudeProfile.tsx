import React from 'react';

export interface ProfileCheckpoint {
  id: number;
  seq: number;
  name: string;
  altitudeM: number;
  distanceKm: number;
  cutoff?: string;
  isCurrent?: boolean;
  isCompleted?: boolean;
}

interface AltitudeProfileProps {
  checkpoints?: ProfileCheckpoint[];
  currentCheckpointId?: number;
  groupDots?: { id: string; checkpointId: number; label: string }[];
}

const DEFAULT_PROFILE: ProfileCheckpoint[] = [
  { id: 1, seq: 1, name: 'Hadsar', altitudeM: 2100, distanceKm: 0.0, cutoff: '14:00' },
  { id: 2, seq: 2, name: 'Dhancho', altitudeM: 3000, distanceKm: 6.0, cutoff: '15:00' },
  { id: 3, seq: 3, name: 'Gaurikund', altitudeM: 3850, distanceKm: 11.5, cutoff: '16:30' },
  { id: 4, seq: 4, name: 'Dal Lake', altitudeM: 4080, distanceKm: 13.0, cutoff: '17:30' }
];

export const AltitudeProfile: React.FC<AltitudeProfileProps> = ({
  checkpoints = DEFAULT_PROFILE,
  currentCheckpointId = 2,
  groupDots = []
}) => {
  const width = 640;
  const height = 270;
  const paddingX = 50;
  const paddingTop = 40;
  const paddingBottom = 75;

  const minAlt = Math.min(...checkpoints.map(c=>c.altitudeM))-200;
  const maxAlt = Math.max(...checkpoints.map(c=>c.altitudeM))+200;
  const maxDist = Math.max(1,...checkpoints.map(c=>c.distanceKm));

  const getX = (distKm: number) => paddingX + (distKm / maxDist) * (width - 2 * paddingX);
  const getY = (altM: number) => height - paddingBottom - ((altM - minAlt) / (maxAlt - minAlt)) * (height - paddingTop - paddingBottom);

  // Generate path data
  const points = checkpoints.map(cp => ({ x: getX(cp.distanceKm), y: getY(cp.altitudeM), ...cp }));
  const pathD = points.reduce((acc, pt, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${pt.x} ${pt.y}`, '');
  const areaD = `${pathD} L ${points[points.length - 1].x} ${height - paddingBottom} L ${points[0].x} ${height - paddingBottom} Z`;

  const currentPt = points.find(p => p.id === currentCheckpointId);

  return (
    <div tabIndex={0} aria-label="Scrollable altitude profile" style={{ width: '100%', overflowX: 'auto', background: 'var(--paper)', border: 'var(--border-hairline)', borderRadius: 'var(--radius)', padding: 'var(--space-2)' }}>
      <svg 
        viewBox={`0 0 ${width} ${height}`} 
        style={{ width: '100%', height: 'auto', display: 'block', minWidth: '480px' }}
        role="img"
        aria-label="Trail elevation altitude profile"
      >
        <defs>
          <linearGradient id="profileGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2F4B3A" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#2F4B3A" stopOpacity="0.04" />
          </linearGradient>
        </defs>

        {/* Altitude Guide Lines */}
        {[2000, 3000, 4000].map(alt => (
          <g key={alt}>
            <line 
              x1={paddingX} 
              y1={getY(alt)} 
              x2={width - paddingX} 
              y2={getY(alt)} 
              stroke="var(--line)" 
              strokeDasharray="3 3" 
              strokeWidth="1" 
            />
            <text 
              x={paddingX - 8} 
              y={getY(alt) + 4} 
              textAnchor="end" 
              fontSize="10" 
              fill="var(--ink-2)" 
              fontFamily="var(--font-mono)"
            >
              {alt}m
            </text>
          </g>
        ))}

        {/* Shaded Area Under Mountain Ridge */}
        <path d={areaD} fill="var(--paper-2)" />

        {/* Mountain Ridge Profile Line */}
        <path d={pathD} fill="none" stroke="var(--deodar)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

        {/* Checkpoint Markers and Labels */}
        {points.map((pt,index) => {
          const isCurrent = pt.id === currentCheckpointId;
          return (
            <g key={pt.id}>
              {/* Checkpoint Tick Line */}
              <line 
                x1={pt.x} 
                y1={pt.y} 
                x2={pt.x} 
                y2={height - paddingBottom} 
                stroke="var(--line)" 
                strokeWidth="1" 
              />
              
              {/* Node Circle */}
              <circle 
                cx={pt.x} 
                cy={pt.y} 
                r={isCurrent ? 6 : 4} 
                fill={isCurrent ? 'var(--accent)' : 'var(--paper)'} 
                stroke={isCurrent ? '#FFFFFF' : 'var(--deodar)'} 
                strokeWidth={isCurrent ? 2 : 1.5} 
              />

              {/* Checkpoint Name */}
              <text 
                x={pt.x} 
                y={height - paddingBottom + 16 + (index % 2)*30} 
                textAnchor="middle" 
                fontSize="11" 
                fontWeight={isCurrent ? '700' : '500'} 
                fill={isCurrent ? 'var(--ink)' : 'var(--ink-2)'}
                fontFamily="var(--font-sans)"
              >
                {pt.name}
              </text>

              {/* Altitude Label */}
              <text 
                x={pt.x} 
                y={pt.y - 12} 
                textAnchor="middle" 
                fontSize="10" 
                fontFamily="var(--font-mono)" 
                fill="var(--ink)"
                fontWeight="600"
              >
                {pt.altitudeM}m
              </text>

              {/* Cutoff Flag if applicable */}
              {pt.cutoff && (
                <text 
                  x={pt.x} 
                  y={height - paddingBottom + 28 + (index % 2)*30} 
                  textAnchor="middle" 
                  fontSize="9" 
                  fontFamily="var(--font-mono)" 
                  fill="var(--watch)"
                  fontWeight="600"
                >
                  By {pt.cutoff}
                </text>
              )}
            </g>
          );
        })}

        {/* You Are Here Pin */}
        {currentPt && (
          <g transform={`translate(${currentPt.x}, ${currentPt.y - 28})`}>
            <rect 
              x="-42" 
              y="-14" 
              width="84" 
              height="18" 
              rx="3" 
              fill="var(--accent)" 
            />
            <text 
              x="0" 
              y="-1" 
              textAnchor="middle" 
              fontSize="9" 
              fontWeight="700" 
              fill="#FFFFFF"
              letterSpacing="0.05em"
              fontFamily="var(--font-sans)"
            >
              LAST CHECK-IN
            </text>
            <polygon points="-4,4 4,4 0,9" fill="var(--accent)" />
          </g>
        )}

        {/* Control Room Live Group Dots (if any) */}
        {groupDots.map((dot, idx) => {
          const pt = points.find(p => p.id === dot.checkpointId);
          if (!pt) return null;
          return (
            <circle 
              key={idx} 
              cx={pt.x + (idx % 3 - 1) * 8} 
              cy={pt.y + 12 + Math.floor(idx / 3) * 8} 
              r="3.5" 
              fill="var(--accent)" 
              stroke="#FFFFFF" 
              strokeWidth="1"
            >
              <title>{dot.label}</title>
            </circle>
          );
        })}
      </svg>
    </div>
  );
};
