import { ReactNode } from 'react';
import SettingsNav from './SettingsNav';
import styles from '../styles/settings.module.css';

type Props = {
  children: ReactNode;
};

const SettingsLayout = ({ children }: Props) => (
  <div className={styles.settingsContainer}>
    <SettingsNav />
    <main className={styles.settingsContent}>{children}</main>
  </div>
);

export default SettingsLayout;
