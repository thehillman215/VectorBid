import React from 'react';

interface PersonaSelectProps {
  value: string;
  onChange: (value: string) => void;
}

const PERSONAS = [
  { value: 'family_first', label: 'Family First' },
  { value: 'money_maker', label: 'Money Maker' },
  { value: 'commuter_friendly', label: 'Commuter Friendly' },
];

export default function PersonaSelect({ value, onChange }: PersonaSelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{ padding: '0.5rem', border: '1px solid #ccc', borderRadius: 4 }}
    >
      <option value="">Select persona</option>
      {PERSONAS.map((p) => (
        <option key={p.value} value={p.value}>
          {p.label}
        </option>
      ))}
    </select>
  );
}
