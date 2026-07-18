'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
    if (res.ok) {
      router.push('/login');
    } else {
      const data = await res.json();
      setError(data.error);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10">
      <h1 className="text-3xl font-bold mb-6">Register</h1>
      {error && <div className="text-red-500 mb-4">{error}</div>}
      <form onSubmit={handleRegister} className="space-y-4">
        <input className="w-full p-2 border rounded" type="text" placeholder="Name" value={name} onChange={e => setName(e.target.value)} required />
        <input className="w-full p-2 border rounded" type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
        <input className="w-full p-2 border rounded" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
        <button className="w-full bg-blue-600 text-white p-2 rounded" type="submit">Register</button>
      </form>
      <p className="mt-4">
        Already have an account? <Link href="/login" className="text-blue-500 hover:underline">Login</Link>
      </p>
    </div>
  );
}
