export const hasConsent = (): boolean => {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem('vb-consent') === '1';
};

export const giveConsent = () => {
  if (typeof window === 'undefined') return;
  localStorage.setItem('vb-consent', '1');
};
