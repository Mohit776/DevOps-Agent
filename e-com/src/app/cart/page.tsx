'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Cart() {
  const [cart, setCart] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    fetch('/api/cart')
      .then(res => res.json())
      .then(data => {
        if (data.error) router.push('/login');
        else setCart(data.cart);
      });
  }, [router]);

  const updateQuantity = async (productId: string, quantity: number) => {
    await fetch('/api/cart', {
      method: 'PUT',
      body: JSON.stringify({ productId, quantity })
    });
    window.location.reload();
  };

  const placeOrder = async () => {
    const res = await fetch('/api/orders', { method: 'POST' });
    if (res.ok) {
      alert('Order placed successfully!');
      router.push('/orders');
    } else {
      alert('Failed to place order');
    }
  };

  if (!cart) return <div>Loading...</div>;

  return (
    <div className="bg-white p-6 rounded shadow">
      <h1 className="text-3xl font-bold mb-6">Your Cart</h1>
      {cart.items?.length === 0 ? (
        <p>Your cart is empty.</p>
      ) : (
        <div>
          {cart.items.map((item: any) => (
            <div key={item.product._id} className="flex justify-between items-center border-b py-4">
              <div className="flex items-center gap-4">
                <img src={item.product.image} alt={item.product.name} className="w-16 h-16 object-cover rounded" />
                <div>
                  <h3 className="font-bold">{item.product.name}</h3>
                  <p>${item.product.price}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <button onClick={() => updateQuantity(item.product._id, item.quantity - 1)} className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300">-</button>
                <span className="font-bold">{item.quantity}</span>
                <button onClick={() => updateQuantity(item.product._id, item.quantity + 1)} className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300">+</button>
              </div>
            </div>
          ))}
          <div className="mt-6 flex justify-end">
            <button onClick={placeOrder} className="px-6 py-3 bg-green-600 text-white rounded hover:bg-green-700">
              Place Order
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
