import { useState } from 'react';
import SettingsLayout from '../../components/SettingsLayout';

const CareerSettings = () => {
  const [desiredBase, setDesiredBase] = useState('');
  const [desiredAircraft, setDesiredAircraft] = useState('');

  return (
    <SettingsLayout>
      <h1>Career Preferences</h1>
      <form>
        <label>
          Preferred Base
          <input
            type="text"
            value={desiredBase}
            onChange={(e) => setDesiredBase(e.target.value)}
          />
        </label>
        <br />
        <label>
          Desired Aircraft
          <input
            type="text"
            value={desiredAircraft}
            onChange={(e) => setDesiredAircraft(e.target.value)}
          />
        </label>
      </form>
    </SettingsLayout>
  );
};

export default CareerSettings;
