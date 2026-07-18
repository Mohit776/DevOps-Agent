"use client";

import React from "react";
import { Product } from "../data/products";
import { useCart } from "../context/CartContext";

interface ProductCardProps {
  product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
  const { addToCart } = useCart();

  return (
    <div className="group relative flex flex-col bg-zinc-900 rounded-2xl overflow-hidden border border-white/5 transition-all duration-300 hover:border-white/20 hover:shadow-[0_0_40px_rgba(59,130,246,0.15)] hover:-translate-y-1">
      <div className="relative aspect-square overflow-hidden bg-zinc-800">
        <img
          src={product.image}
          alt={product.name}
          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-zinc-900/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      </div>
      
      <div className="flex flex-col flex-grow p-6">
        <div className="flex items-start justify-between gap-4 mb-2">
          <h3 className="text-lg font-semibold text-white leading-tight">
            {product.name}
          </h3>
          <span className="text-blue-400 font-medium whitespace-nowrap">
            ${product.price.toFixed(2)}
          </span>
        </div>
        
        <p className="text-sm text-zinc-400 mb-6 flex-grow">
          {product.description}
        </p>
        
        <button
          onClick={() => addToCart(product)}
          className="w-full py-3 px-4 bg-white/5 hover:bg-white/10 text-white rounded-xl font-medium transition-all duration-200 active:scale-95 flex items-center justify-center gap-2 border border-white/10 hover:border-white/20"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M5 12h14" />
            <path d="M12 5v14" />
          </svg>
          Add to Cart
        </button>
      </div>
    </div>
  );
}
