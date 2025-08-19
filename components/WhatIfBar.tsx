import React from 'react';

interface WhatIfBarProps {
  weights: Record<string, number>;
  onChange: (w: Record<string, number>) => void;
}

export default function WhatIfBar({ weights, onChange }: WhatIfBarProps) {
  const handle = (key: string, value: number) => {
    onChange({ ...weights, [key]: value });
  };

  return (
    <div>
      {Object.entries(weights).map(([key, value]) => (
        <div key={key} style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
          <label style={{ width: '10rem' }}>{key}</label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.1}
            value={value}
            onChange={(e) => handle(key, parseFloat(e.target.value))}
            style={{ flex: 1 }}
          />
          <span style={{ marginLeft: '0.5rem', width: '2rem', textAlign: 'right' }}>{value.toFixed(1)}</span>
        </div>
      ))}
    </div>
  );
}
