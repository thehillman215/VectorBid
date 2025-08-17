import { useState } from 'react';
import styles from '../styles/landing.module.css';
import { track } from '../lib/analytics';

const ROISection = () => {
  const [hours, setHours] = useState(5);
  const [rate, setRate] = useState(100);
  const saved = hours;
  const value = saved * rate;

  return (
    <section className={styles.section}>
      <div className={styles.container}>
        <h2>Get your time back</h2>
        <label>
          Hours you typically spend bidding: {hours} hrs
          <input type="range" min="0" max="10" value={hours} onChange={(e) => setHours(Number(e.target.value))} />
        </label>
        <div style={{ marginTop: '1rem' }}>
          <label>
            Value of your time ($/hr):
            <input type="number" className={styles.input} value={rate} onChange={(e) => setRate(Number(e.target.value))} />
          </label>
        </div>
        <p style={{ marginTop: '1rem' }}>VectorBid saves you ~{saved} hours per month (${value.toFixed(0)} value).</p>
        <a href="#cta" className={styles.btnPrimary} onClick={() => track('pricing_cta_click')}>Get my time back</a>
      </div>
    </section>
  );
};

export default ROISection;
