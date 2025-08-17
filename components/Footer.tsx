import styles from '../styles/landing.module.css';

const Footer = () => (
  <footer className={styles.footer}>
    <div className={styles.container}>
      <p>
        <a href="/terms">Terms</a> | <a href="/privacy">Privacy</a> | <a href="/contact">Contact</a> | <a href="/status">Status</a>
      </p>
      <p className={styles.muted}>
        © {new Date().getFullYear()} VectorBid. PBS is a trademark of its respective owners. No airline endorsement implied.
      </p>
    </div>
  </footer>
);

export default Footer;
