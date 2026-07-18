import { NextResponse } from 'next/server';
import { removeSession } from '@/lib/auth';
import { logger } from '@/lib/logger';

export async function POST() {
  try {
    await removeSession();
    logger.info('User logged out');
    return NextResponse.json({ message: 'Logged out' });
  } catch (error) {
    logger.error('Logout error', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
