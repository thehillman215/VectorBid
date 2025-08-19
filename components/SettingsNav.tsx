import Link from 'next/link';
import styles from '../styles/settings.module.css';

const SettingsNav = () => (
  <nav className={styles.settingsNav}>
    <ul>
      <li><Link href="/settings/security">Security</Link></li>
      <li><Link href="/settings/communication">Communication Preferences</Link></li>
      <li><Link href="/settings/career">Career Preferences</Link></li>
      <li><Link href="/settings/subscription">Subscription Info</Link></li>
      <li><Link href="/settings/billing">Billing History</Link></li>
    </ul>
  </nav>
);

export default SettingsNav;
