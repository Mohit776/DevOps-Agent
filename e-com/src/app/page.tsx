import Link from 'next/link';

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-5xl font-bold mb-4">Welcome to Simple E-Commerce</h1>
      <p className="text-xl mb-8 text-gray-600">A reliable target application for AI DevOps monitoring.</p>
      <div className="space-x-4">
        <Link href="/products" className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700">
          View Products
        </Link>
        <Link href="/login" className="px-6 py-3 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">
          Login
        </Link>
      </div>
    </div>
  );
}
