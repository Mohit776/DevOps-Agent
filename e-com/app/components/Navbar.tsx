"use client";

import React from "react";
import Link from "next/link";
import { useCart } from "../context/CartContext";

export default function Navbar() {
  const { cartCount, setIsCartOpen, isCartOpen } = useCart();

  return (
    <nav className="fixed top-0 left-0 right-0 z-40 bg-zinc-950/70 backdrop-blur-md border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex-shrink-0">
            <Link href="/" className="text-xl font-bold tracking-tighter text-white">
              LUMINA<span className="text-blue-500">.</span>
            </Link>
          </div>
          <div className="flex items-center">
            <button
              onClick={() => setIsCartOpen(!isCartOpen)}
              className="relative p-2 text-zinc-300 hover:text-white transition-colors focus:outline-none"
              aria-label="Cart"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="8" cy="21" r="1" />
                <circle cx="19" cy="21" r="1" />
                <path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12" />
              </svg>
              {cartCount > 0 && (
                <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/4 -translate-y-1/4 bg-blue-500 rounded-full">
                  {cartCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
