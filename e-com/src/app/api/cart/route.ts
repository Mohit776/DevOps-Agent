import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import { Cart } from '@/models/Cart';
import { getSession } from '@/lib/auth';
import { logger } from '@/lib/logger';
import mongoose from 'mongoose';

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    await connectDB();
    let cart = await Cart.findOne({ user: session.user.id }).populate('items.product');
    if (!cart) {
      cart = await Cart.create({ user: session.user.id, items: [] });
    }
    return NextResponse.json({ cart });
  } catch (error) {
    logger.error('Error fetching cart', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { productId, quantity } = await req.json();
    if (!productId || !quantity) return NextResponse.json({ error: 'Missing fields' }, { status: 400 });

    await connectDB();
    let cart = await Cart.findOne({ user: session.user.id });
    if (!cart) {
      cart = new Cart({ user: session.user.id, items: [] });
    }

    const itemIndex = cart.items.findIndex((item) => item.product.toString() === productId);
    if (itemIndex > -1) {
      cart.items[itemIndex].quantity += quantity;
    } else {
      cart.items.push({ product: new mongoose.Types.ObjectId(productId), quantity });
    }

    await cart.save();
    logger.info('Cart updated', { userId: session.user.id });
    
    await cart.populate('items.product');
    return NextResponse.json({ cart });
  } catch (error) {
    logger.error('Error adding to cart', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function PUT(req: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { productId, quantity } = await req.json();
    if (!productId || quantity === undefined) return NextResponse.json({ error: 'Missing fields' }, { status: 400 });

    await connectDB();
    const cart = await Cart.findOne({ user: session.user.id });
    if (!cart) return NextResponse.json({ error: 'Cart not found' }, { status: 404 });

    const itemIndex = cart.items.findIndex((item) => item.product.toString() === productId);
    if (itemIndex > -1) {
      if (quantity <= 0) {
        cart.items.splice(itemIndex, 1);
      } else {
        cart.items[itemIndex].quantity = quantity;
      }
      await cart.save();
    }
    await cart.populate('items.product');
    return NextResponse.json({ cart });
  } catch (error) {
    logger.error('Error updating cart', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function DELETE(req: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const url = new URL(req.url);
    const productId = url.searchParams.get('productId');
    
    if (!productId) return NextResponse.json({ error: 'Missing productId' }, { status: 400 });

    await connectDB();
    const cart = await Cart.findOne({ user: session.user.id });
    if (!cart) return NextResponse.json({ error: 'Cart not found' }, { status: 404 });

    cart.items = cart.items.filter((item) => item.product.toString() !== productId);
    await cart.save();
    await cart.populate('items.product');
    return NextResponse.json({ cart });
  } catch (error) {
    logger.error('Error removing from cart', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
