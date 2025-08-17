import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false });
  }

  const { name, email, airline, notes } = req.body || {};
  if (!email) {
    return res.status(400).json({ ok: false, error: 'Email required' });
  }

  console.log('lead', { name, email, airline, notes });
  // TODO: integrate with provider
  return res.status(200).json({ ok: true });
}
