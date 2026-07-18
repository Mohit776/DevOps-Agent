'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Orders() {
  const [orders, setOrders] = useState<any[]>([]);
  const router = useRouter();

  useEffect(() => {
    fetch('/api/orders')
      .then(res => res.json())
      .then(data => {
        if (data.error) router.push('/login');
        else setOrders(data.orders || []);
      });
  }, [router]);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Your Orders</h1>
      {orders.length === 0 ? (
        <p>You have no orders.</p>
      ) : (
        <div className="space-y-6">
          {orders.map((order: any) => (
            <div key={order._id} className="border p-4 rounded shadow bg-white">
              <div className="flex justify-between items-center mb-4">
                <h2 className="font-bold text-lg">Order ID: {order._id}</h2>
                <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded font-semibold">{order.status}</span>
              </div>
              <p className="text-gray-800 font-bold mb-2">Total: ${order.total}</p>
              <div className="space-y-2 mt-4 border-t pt-4">
                {order.products.map((p: any) => (
                  <div key={p.product?._id || Math.random()} className="flex justify-between text-sm text-gray-700">
                    <span>{p.product?.name || 'Unknown Product'} (x{p.quantity})</span>
                    <span>${p.price * p.quantity}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
