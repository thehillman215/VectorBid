import styles from '../styles/landing.module.css';
import { track } from '../lib/analytics';

const Pricing = () => (
  <section className={styles.section}>
    <div className={styles.container}>
      <h2>Pricing</h2>
      <div className={styles.priceCard}>
        <h3>Pro</h3>
        <p><strong>$29</strong>/mo or <strong>$290</strong>/yr</p>
        <ul style={{ textAlign: 'left', margin: '1rem 0' }}>
          <li>Unlimited bid runs</li>
          <li>Persona templates</li>
          <li>FAR/contract checks</li>
          <li>Export to PBS syntax</li>
        </ul>
        <a href="/signup" className={styles.btnPrimary} onClick={() => track('pricing_cta_click')}>Start free trial</a>
        <p className={styles.muted} style={{ marginTop: '0.5rem' }}>Payments disabled in this environment.</p>
      </div>
    </div>
  </section>
);

export default Pricing;
