import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import { Product } from '@/models/Product';
import { getSession } from '@/lib/auth';
import { logger } from '@/lib/logger';

export async function GET() {
  try {
    await connectDB();
    const products = await Product.find({}).sort({ createdAt: -1 });
    return NextResponse.json({ products });
  } catch (error) {
    logger.error('Error fetching products', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const session = await getSession();
    if (!session || session.user.role !== 'admin') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
    }

    await connectDB();
    const data = await req.json();
    const product = await Product.create(data);
    logger.info('Product created', { productId: product._id, admin: session.user.email });
    return NextResponse.json({ product }, { status: 201 });
  } catch (error) {
    logger.error('Error creating product', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
