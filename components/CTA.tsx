import styles from '../styles/landing.module.css';
import { track } from '../lib/analytics';
import LeadForm from './LeadForm';

const CTA = () => (
  <section id="cta" className={styles.section}>
    <div className={styles.container}>
      <h2>Ready to bid like a pro?</h2>
      <div className={styles.formRow}>
        <a href="/signup" className={styles.btnPrimary} onClick={() => track('hero_cta_click')}>Start free trial</a>
        <a href="#" className={styles.btnSecondary} onClick={() => track('demo_open')}>See demo</a>
      </div>
      <LeadForm />
    </div>
  </section>
);

export default CTA;
