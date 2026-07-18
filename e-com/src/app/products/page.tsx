'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function Products() {
  const [products, setProducts] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/products')
      .then(res => res.json())
      .then(data => setProducts(data.products || []));
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Products</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {products.map(product => (
          <div key={product._id} className="border p-4 rounded shadow bg-white">
            <img src={product.image} alt={product.name} className="w-full h-48 object-cover mb-4" />
            <h2 className="text-xl font-bold">{product.name}</h2>
            <p className="text-gray-600 mb-2">${product.price}</p>
            <Link href={`/products/${product._id}`} className="text-blue-500 hover:underline">
              View Details
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
