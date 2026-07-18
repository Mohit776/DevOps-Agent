'use client';

import { useEffect, useState } from 'react';

export default function Admin() {
  const [products, setProducts] = useState<any[]>([]);
  const [form, setForm] = useState({ name: '', description: '', price: 0, image: '', stock: 100 });
  const [editingId, setEditingId] = useState<string | null>(null);

  const fetchProducts = () => {
    fetch('/api/products').then(res => res.json()).then(data => setProducts(data.products || []));
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const url = editingId ? `/api/products/${editingId}` : '/api/products';
    const method = editingId ? 'PUT' : 'POST';

    const res = await fetch(url, {
      method,
      body: JSON.stringify(form)
    });

    if (res.ok) {
      setForm({ name: '', description: '', price: 0, image: '', stock: 100 });
      setEditingId(null);
      fetchProducts();
    } else {
      alert('Failed to save product. Are you an admin?');
    }
  };

  const handleEdit = (product: any) => {
    setForm(product);
    setEditingId(product._id);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure?')) return;
    const res = await fetch(`/api/products/${id}`, { method: 'DELETE' });
    if (res.ok) {
      fetchProducts();
    } else {
      alert('Failed to delete product');
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-6">
      <div>
        <h1 className="text-3xl font-bold mb-6">Admin - Manage Products</h1>
        <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded shadow border">
          <input className="w-full p-2 border rounded" type="text" placeholder="Name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required />
          <textarea className="w-full p-2 border rounded" placeholder="Description" value={form.description} onChange={e => setForm({...form, description: e.target.value})} required />
          <input className="w-full p-2 border rounded" type="number" placeholder="Price" value={form.price} onChange={e => setForm({...form, price: Number(e.target.value)})} required />
          <input className="w-full p-2 border rounded" type="text" placeholder="Image URL (e.g. https://via.placeholder.com/150)" value={form.image} onChange={e => setForm({...form, image: e.target.value})} required />
          <input className="w-full p-2 border rounded" type="number" placeholder="Stock" value={form.stock} onChange={e => setForm({...form, stock: Number(e.target.value)})} required />
          <button className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700" type="submit">
            {editingId ? 'Update Product' : 'Add Product'}
          </button>
          {editingId && (
            <button type="button" onClick={() => { setEditingId(null); setForm({ name: '', description: '', price: 0, image: '', stock: 100 }); }} className="w-full bg-gray-500 text-white p-2 rounded hover:bg-gray-600 mt-2">
              Cancel Edit
            </button>
          )}
        </form>
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4">Product List</h2>
        <div className="space-y-4">
          {products.map(product => (
            <div key={product._id} className="border p-4 rounded shadow bg-white flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h3 className="font-bold">{product.name}</h3>
                <p className="text-gray-600">${product.price} | Stock: {product.stock}</p>
              </div>
              <div className="space-x-2 flex">
                <button onClick={() => handleEdit(product)} className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600">Edit</button>
                <button onClick={() => handleDelete(product._id)} className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
