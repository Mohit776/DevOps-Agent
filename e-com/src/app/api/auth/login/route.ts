import { NextResponse } from 'next/server';
import bcrypt from 'bcryptjs';
import { connectDB } from '@/lib/db';
import { User } from '@/models/User';
import { setSession } from '@/lib/auth';
import { logger } from '@/lib/logger';

export async function POST(req: Request) {
  try {
    await connectDB();
    const { email, password } = await req.json();

    const user = await User.findOne({ email });
    if (!user || !(await bcrypt.compare(password, user.password || ''))) {
      return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    }

    const userData = { id: user._id, email: user.email, name: user.name, role: user.role };
    await setSession(userData);
    
    logger.info('User logged in', { email: user.email });

    return NextResponse.json({ message: 'Logged in', user: userData });
  } catch (error) {
    logger.error('Login error', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
