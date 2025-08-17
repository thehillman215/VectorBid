import styles from '../styles/landing.module.css';

const steps = [
  { title: 'Tell us what you want', text: 'Set your profile and natural language preferences.' },
  { title: 'We auto-generate layered PBS commands', text: 'Smart engine builds compliant layers.' },
  { title: 'Review conflicts, adjust instantly', text: 'See issues and tweak with one click.' },
  { title: 'Copy/paste into PBS', text: 'Export ready-to-use syntax.' },
];

const HowItWorks = () => (
  <section className={styles.section}>
    <div className={styles.container}>
      <h2>How it works</h2>
      <ol className={styles.grid} style={{ counterReset: 'step', gridTemplateColumns: 'repeat(auto-fit,minmax(250px,1fr))' }}>
        {steps.map((s, i) => (
          <li key={s.title} className={styles.card} style={{ listStyle: 'none' }}>
            <p><strong>Step {i + 1}: {s.title}</strong></p>
            <p className={styles.muted}>{s.text}</p>
          </li>
        ))}
      </ol>
    </div>
  </section>
);

export default HowItWorks;
