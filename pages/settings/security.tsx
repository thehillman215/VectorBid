import { useState } from 'react';
import SettingsLayout from '../../components/SettingsLayout';

const SecuritySettings = () => {
  const [twoFactor, setTwoFactor] = useState(false);

  return (
    <SettingsLayout>
      <h1>Security Settings</h1>
      <form>
        <label>
          <input
            type="checkbox"
            checked={twoFactor}
            onChange={(e) => setTwoFactor(e.target.checked)}
          />
          Enable two-factor authentication
        </label>
      </form>
    </SettingsLayout>
  );
};

export default SecuritySettings;
