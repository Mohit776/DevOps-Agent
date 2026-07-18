import type { Metadata } from "next";
import "./globals.css";
import Link from 'next/link';

export const metadata: Metadata = {
  title: "Simple E-Commerce",
  description: "Target application for AI DevOps Agent",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen flex flex-col bg-gray-50 text-gray-900">
        <nav className="bg-white shadow p-4">
          <div className="max-w-6xl mx-auto flex justify-between items-center">
            <Link href="/" className="font-bold text-xl text-blue-600">E-Commerce</Link>
            <div className="space-x-4">
              <Link href="/products" className="hover:text-blue-500">Products</Link>
              <Link href="/cart" className="hover:text-blue-500">Cart</Link>
              <Link href="/orders" className="hover:text-blue-500">Orders</Link>
              <Link href="/admin" className="hover:text-blue-500">Admin</Link>
              <Link href="/login" className="hover:text-blue-500">Login</Link>
            </div>
          </div>
        </nav>
        <main className="flex-1 max-w-6xl mx-auto w-full p-4">
          {children}
        </main>
        <footer className="bg-gray-800 text-white p-4 text-center">
          <p>&copy; {new Date().getFullYear()} Simple E-Commerce</p>
        </footer>
      </body>
    </html>
  );
}
