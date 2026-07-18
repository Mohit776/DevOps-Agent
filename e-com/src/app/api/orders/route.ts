import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import { Order } from '@/models/Order';
import { Cart } from '@/models/Cart';
import { getSession } from '@/lib/auth';
import { logger } from '@/lib/logger';

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    await connectDB();
    const orders = await Order.find({ user: session.user.id }).populate('products.product').sort({ createdAt: -1 });
    return NextResponse.json({ orders });
  } catch (error) {
    logger.error('Error fetching orders', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function POST() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    await connectDB();
    const cart = await Cart.findOne({ user: session.user.id }).populate('items.product');
    if (!cart || cart.items.length === 0) {
      return NextResponse.json({ error: 'Cart is empty' }, { status: 400 });
    }

    let total = 0;
    const orderProducts = cart.items.map((item: any) => {
      const price = item.product.price;
      total += price * item.quantity;
      return {
        product: item.product._id,
        quantity: item.quantity,
        price
      };
    });

    const order = await Order.create({
      user: session.user.id,
      products: orderProducts,
      total,
      status: 'pending'
    });

    cart.items = [];
    await cart.save();

    logger.info('Order placed', { orderId: order._id, userId: session.user.id });
    
    return NextResponse.json({ order }, { status: 201 });
  } catch (error) {
    logger.error('Error placing order', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
