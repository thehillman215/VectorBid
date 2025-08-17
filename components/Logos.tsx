import Image from 'next/image';
import styles from '../styles/landing.module.css';

const Logos = () => (
  <section className={styles.section}>
    <div className={styles.container}>
      <div className={styles.logoRow}>
        <Image src="/logo-placeholder.svg" alt="Placeholder logo" width={100} height={40} />
        <Image src="/logo-placeholder.svg" alt="Placeholder logo" width={100} height={40} />
        <Image src="/logo-placeholder.svg" alt="Placeholder logo" width={100} height={40} />
        <Image src="/logo-placeholder.svg" alt="Placeholder logo" width={100} height={40} />
      </div>
      <p className={styles.muted}>For illustration only—VectorBid is not affiliated with airlines.</p>
    </div>
  </section>
);

export default Logos;
