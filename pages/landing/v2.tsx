import Head from 'next/head';
import { useEffect, useState } from 'react';
import HeroV2 from '../../components/HeroV2';
import Logos from '../../components/Logos';
import Benefits from '../../components/Benefits';
import HowItWorks from '../../components/HowItWorks';
import ROISection from '../../components/ROISection';
import Testimonials from '../../components/Testimonials';
import Pricing from '../../components/Pricing';
import FAQ, { FAQItem } from '../../components/FAQ';
import CTA from '../../components/CTA';
import Footer from '../../components/Footer';
import { initAnalytics } from '../../lib/analytics';
import { hasConsent, giveConsent } from '../../lib/consent';
import styles from '../../styles/landing.module.css';

const faqItems: FAQItem[] = [
  { q: 'Is VectorBid aware of PBS 2.0?', a: 'Yes. Our logic understands PBS 2.0 rules and formats.' },
  { q: 'Which airlines do you support?', a: 'We are starting with United and adding more carriers soon.' },
  { q: 'How accurate are the suggestions?', a: 'We follow your contract and FARs but final responsibility lies with the pilot.' },
  { q: 'Do you store my data?', a: 'Preferences are stored securely and never shared.' },
  { q: 'Is there a refund policy?', a: 'We offer a no-questions-asked refund within 30 days.' },
  { q: 'Are you affiliated with any airline or PBS vendor?', a: 'No. VectorBid is an independent tool and not endorsed by any airline or PBS vendor.' },
  { q: 'How do I get support?', a: 'Email us anytime at support@vectorbid.com.' },
  { q: 'What about data privacy?', a: 'Your data stays with us and is used only to improve your bids.' },
];

const faqJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: faqItems.map((f) => ({
    '@type': 'Question',
    name: f.q,
    acceptedAnswer: { '@type': 'Answer', text: f.a },
  })),
};

export default function LandingV2() {
  const [consent, setConsent] = useState(false);

  useEffect(() => {
    initAnalytics();
    setConsent(hasConsent());
  }, []);

  return (
    <>
      <Head>
        <title>VectorBid — Smarter PBS bids with AI</title>
        <meta name="description" content="Precision PBS bidding with AI-driven contract and FAR awareness." />
        <meta property="og:title" content="VectorBid — Smarter PBS bids with AI" />
        <meta property="og:description" content="Let VectorBid craft bids that maximise time at home." />
        <meta property="og:image" content="/og-vectorbid.svg" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:image" content="/og-vectorbid.svg" />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }} />
      </Head>
      <HeroV2 />
      <Logos />
      <ROISection />
      <Benefits />
      <HowItWorks />
      <Testimonials />
      <Pricing />
      <FAQ items={faqItems} />
      <CTA />
      <Footer />
      {process.env.NEXT_PUBLIC_ANALYTICS === '1' && !consent && (
        <div className={styles.consent}>
          <p>This site uses cookies for analytics.</p>
          <button className={styles.btnPrimary} onClick={() => { giveConsent(); setConsent(true); }}>OK</button>
        </div>
      )}
    </>
  );
}
