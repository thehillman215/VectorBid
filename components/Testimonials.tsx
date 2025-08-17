import styles from '../styles/landing.module.css';

const testimonials = [
  { quote: 'VectorBid nailed my weekends off on the first try.', name: 'Alex, FO' },
  { quote: 'I spend half the time building bids now.', name: 'Jamie, Captain' },
  { quote: 'Finally understand the tradeoffs before submitting.', name: 'Riley, FO' },
];

const Testimonials = () => (
  <section className={styles.section}>
    <div className={`${styles.container} ${styles.testimonials}`}>
      {testimonials.map((t) => (
        <blockquote key={t.quote} className={styles.card}>
          <p>"{t.quote}"</p>
          <footer className={styles.muted}>— {t.name}</footer>
        </blockquote>
      ))}
    </div>
  </section>
);

export default Testimonials;
