import styles from '../styles/landing.module.css';

const items = [
  { title: 'Save hours every bid cycle', text: 'Automate layer creation and validation.' },
  { title: 'Natural language → valid PBS layers', text: 'Describe what you want and get syntax instantly.' },
  { title: 'Contract & FAR-aware suggestions', text: 'We flag conflicts before you submit.' },
  { title: 'Persona templates for common strategies', text: 'Jumpstart with proven approaches.' },
  { title: 'Transparent tradeoffs before you submit', text: 'See what each choice costs.' },
];

const Benefits = () => (
  <section className={styles.section}>
    <div className={`${styles.container} ${styles.grid}`} style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))' }}>
      {items.map((b) => (
        <div key={b.title} className={styles.card}>
          <p><strong>{b.title}</strong></p>
          <p className={styles.muted}>{b.text}</p>
        </div>
      ))}
    </div>
  </section>
);

export default Benefits;
