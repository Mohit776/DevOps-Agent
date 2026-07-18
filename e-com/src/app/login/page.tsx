'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (res.ok) {
      router.push('/');
      router.refresh();
    } else {
      const data = await res.json();
      setError(data.error);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10">
      <h1 className="text-3xl font-bold mb-6">Login</h1>
      {error && <div className="text-red-500 mb-4">{error}</div>}
      <form onSubmit={handleLogin} className="space-y-4">
        <input className="w-full p-2 border rounded" type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
        <input className="w-full p-2 border rounded" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
        <button className="w-full bg-blue-600 text-white p-2 rounded" type="submit">Login</button>
      </form>
      <p className="mt-4">
        Don't have an account? <Link href="/register" className="text-blue-500 hover:underline">Register</Link>
      </p>
    </div>
  );
}
