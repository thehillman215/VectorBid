import { useState } from 'react';
import PersonaSelect from '../components/PersonaSelect';
import PreferencePreview from '../components/PreferencePreview';
import WhatIfBar from '../components/WhatIfBar';

export default function Onboarding() {
  const [persona, setPersona] = useState('');
  const [weights, setWeights] = useState({
    weekend_weight: 0.5,
    credit_weight: 0.5,
    trip_weight: 0.5,
  });

  return (
    <div style={{ maxWidth: '40rem', margin: '0 auto', padding: '1rem' }}>
      <h1>Onboarding</h1>
      <div style={{ marginBottom: '1rem' }}>
        <PersonaSelect value={persona} onChange={setPersona} />
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <PreferencePreview persona={persona} />
      </div>
      <WhatIfBar weights={weights} onChange={setWeights} />
    </div>
  );
}
