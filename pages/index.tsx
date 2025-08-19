import type { NextPage } from 'next';
import V1 from './landing/v1';
import V2 from './landing/v2';

const variants: Record<string, NextPage> = {
  v1: V1,
  v2: V2,
};

const current = process.env.NEXT_PUBLIC_LANDING || 'v1';
const LandingPage = variants[current] || V1;

export default LandingPage;
