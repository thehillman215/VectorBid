import { FormEvent, useState } from 'react';
import styles from '../styles/landing.module.css';
import { track } from '../lib/analytics';

const LeadForm = () => {
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [form, setForm] = useState({ name: '', email: '', airline: '', notes: '' });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.email) return;
    try {
      const res = await fetch('/api/lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        setStatus('success');
        track('lead_submit');
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }
  };

  return (
    <form onSubmit={handleSubmit} className={styles.formRow} aria-label="Lead capture">
      <input
        type="text"
        placeholder="Name"
        value={form.name}
        onChange={(e) => setForm({ ...form, name: e.target.value })}
        className={styles.input}
        aria-label="Name"
      />
      <input
        type="email"
        placeholder="Email"
        value={form.email}
        onChange={(e) => setForm({ ...form, email: e.target.value })}
        className={styles.input}
        required
        aria-label="Email"
      />
      <input
        type="text"
        placeholder="Airline"
        value={form.airline}
        onChange={(e) => setForm({ ...form, airline: e.target.value })}
        className={styles.input}
        aria-label="Airline"
      />
      <button type="submit" className={styles.btnPrimary}>Join waitlist</button>
      {status === 'success' && <span role="status">Thanks!</span>}
      {status === 'error' && <span role="alert">Something went wrong.</span>}
    </form>
  );
};

export default LeadForm;
