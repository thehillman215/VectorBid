export const initAnalytics = () => {
  if (process.env.NEXT_PUBLIC_ANALYTICS !== '1' || typeof window === 'undefined') return;
  if (document.getElementById('plausible-script')) return;
  const script = document.createElement('script');
  script.setAttribute('id', 'plausible-script');
  script.setAttribute('data-domain', 'vectorbid.com');
  script.src = 'https://plausible.io/js/script.js';
  script.defer = true;
  document.head.appendChild(script);
};

export const track = (event: string, options?: Record<string, any>) => {
  if (process.env.NEXT_PUBLIC_ANALYTICS !== '1') return;
  (window as any).plausible?.(event, { props: options });
};
