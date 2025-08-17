import { useState } from 'react';
import styles from '../styles/landing.module.css';
import { track } from '../lib/analytics';
import LeadForm from './LeadForm';

const Hero = () => {
  const [showVideo, setShowVideo] = useState(false);

  const openDemo = () => {
    setShowVideo(true);
    track('demo_open');
  };

  return (
    <section className={styles.hero}>
      <div className={styles.container}>
        <h1>Build winning PBS bids in minutes.</h1>
        <p>VectorBid turns your preferences into optimized layers that comply with contract and FARs—so you get more of the schedule you want.</p>
        <div className={styles.formRow}>
          <a href="/signup" className={styles.btnPrimary} onClick={() => track('hero_cta_click')}>Start free trial</a>
          <button onClick={openDemo} className={styles.btnSecondary}>See 2-min demo</button>
        </div>
        <div className={styles.badges}>
          <span className={styles.badge}>PBS 2.0 aware</span>
          <span className={styles.badge}>Contract-aware logic</span>
          <span className={styles.badge}>FAR compliance checks</span>
        </div>
        <p className={styles.muted}>Built with pilots, for pilots.</p>
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

export default Hero;
