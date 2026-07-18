'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function ProductDetails() {
  const params = useParams();
  const router = useRouter();
  const [product, setProduct] = useState<any>(null);

  useEffect(() => {
    fetch(`/api/products/${params.id}`)
      .then(res => res.json())
      .then(data => setProduct(data.product));
  }, [params.id]);

  const addToCart = async () => {
    const res = await fetch('/api/cart', {
      method: 'POST',
      body: JSON.stringify({ productId: product._id, quantity: 1 })
    });
    if (res.ok) {
      alert('Added to cart');
    } else {
      alert('Please login first');
      router.push('/login');
    }
  };

  if (!product) return <div>Loading...</div>;

  return (
    <div className="flex flex-col md:flex-row gap-8 mt-10">
      <img src={product.image} alt={product.name} className="w-full md:w-1/2 object-cover rounded shadow" />
      <div>
        <h1 className="text-4xl font-bold mb-4">{product.name}</h1>
        <p className="text-2xl text-gray-700 mb-4">${product.price}</p>
        <p className="text-gray-600 mb-6">{product.description}</p>
        <button onClick={addToCart} className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700">
          Add to Cart
        </button>
      </div>
    </div>
  );
}
