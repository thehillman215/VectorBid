import styles from '../styles/landing.module.css';

export interface FAQItem { q: string; a: string; }

const FAQ = ({ items }: { items: FAQItem[] }) => (
  <section className={styles.section}>
    <div className={styles.container}>
      <h2>FAQ</h2>
      {items.map((f) => (
        <div key={f.q} className={styles.faqItem}>
          <details>
            <summary>{f.q}</summary>
            <p className={styles.muted}>{f.a}</p>
          </details>
        </div>
      ))}
    </div>
  </section>
);

export default FAQ;
