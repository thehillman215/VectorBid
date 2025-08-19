import { useState } from 'react';
import styles from '../styles/landing.module.css';
import { track } from '../lib/analytics';
import LeadForm from './LeadForm';

const HeroV2 = () => {
  const [showVideo, setShowVideo] = useState(false);

  const openDemo = () => {
    setShowVideo(true);
    track('demo_open');
  };

  return (
    <section className={styles.hero}>
      <div className={styles.container}>
        <h1>Win the schedule you want with AI precision</h1>
        <p>VectorBid reads your contract and preferences to build PBS bids that maximise time at home.</p>
        <div className={styles.formRow}>
          <a href="/signup" className={styles.btnPrimary} onClick={() => track('hero_cta_click')}>Get started free</a>
          <button onClick={openDemo} className={styles.btnSecondary}>Watch demo</button>
        </div>
        <div className={styles.badges}>
          <span className={styles.badge}>Contract & FAR aware</span>
          <span className={styles.badge}>Instant export</span>
          <span className={styles.badge}>Private & secure</span>
        </div>
        <LeadForm />
        {showVideo && (
          <div role="dialog" aria-modal="true" className={styles.section}>
            <button onClick={() => setShowVideo(false)} className={styles.btnSecondary}>Close</button>
            <div style={{ marginTop: '1rem' }}>
              <iframe
                width="560"
                height="315"
                src="https://www.youtube.com/embed/dQw4w9WgXcQ"
                title="Demo video"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

export default HeroV2;
