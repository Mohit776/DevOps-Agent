import { NextResponse } from 'next/server';
import mongoose from 'mongoose';
import { connectDB } from '@/lib/db';
import { logger } from '@/lib/logger';

export async function GET() {
  try {
    await connectDB();
    const isDbConnected = mongoose.connection.readyState === 1;
    
    logger.info('Health check requested', { endpoint: '/api/health' });

    return NextResponse.json({
      status: isDbConnected ? 'healthy' : 'degraded',
      database: isDbConnected ? 'connected' : 'disconnected',
      timestamp: new Date().toISOString()
    }, { status: isDbConnected ? 200 : 503 });
  } catch (error) {
    logger.error('Health check failed', error);
    return NextResponse.json({
      status: 'unhealthy',
      database: 'error',
      timestamp: new Date().toISOString()
    }, { status: 500 });
  }
}
