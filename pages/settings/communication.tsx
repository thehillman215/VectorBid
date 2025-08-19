import { useState } from 'react';
import SettingsLayout from '../../components/SettingsLayout';

const CommunicationSettings = () => {
  const [emailOptIn, setEmailOptIn] = useState(true);
  const [smsOptIn, setSmsOptIn] = useState(false);

  return (
    <SettingsLayout>
      <h1>Communication Preferences</h1>
      <form>
        <label>
          <input
            type="checkbox"
            checked={emailOptIn}
            onChange={(e) => setEmailOptIn(e.target.checked)}
          />
          Email notifications
        </label>
        <br />
        <label>
          <input
            type="checkbox"
            checked={smsOptIn}
            onChange={(e) => setSmsOptIn(e.target.checked)}
          />
          SMS notifications
        </label>
      </form>
    </SettingsLayout>
  );
};

export default CommunicationSettings;
