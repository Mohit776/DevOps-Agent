import React from "react";
import { products } from "./data/products";
import ProductCard from "./components/ProductCard";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-32 pb-20 lg:pt-48 lg:pb-32">
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-black/60 z-10" />
          <img
            src="https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=1600&q=80"
            alt="Hero Background"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-black to-transparent z-20" />
        </div>
        
        <div className="relative z-30 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6">
            Elevate Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">Tech Experience</span>
          </h1>
          <p className="mt-4 max-w-2xl text-xl text-zinc-300 mx-auto mb-10">
            Discover a curated collection of premium gadgets designed for performance, aesthetics, and lifestyle.
          </p>
          <a
            href="#products"
            className="inline-flex items-center justify-center px-8 py-4 text-base font-medium text-white bg-blue-600 border border-transparent rounded-full shadow-sm hover:bg-blue-700 hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all duration-300"
          >
            Shop Now
          </a>
        </div>
      </section>

      {/* Products Grid */}
      <section id="products" className="py-24 bg-black relative z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Featured Collection
            </h2>
            <p className="mt-4 text-zinc-400">
              The tools you need to do your best work, packaged in beautiful, minimalist designs.
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="border-t border-white/10 bg-black py-12 relative z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between">
          <div className="flex items-center gap-2 mb-4 md:mb-0">
            <span className="text-xl font-bold tracking-tighter text-white">
              LUMINA<span className="text-blue-500">.</span>
            </span>
          </div>
          <p className="text-zinc-500 text-sm">
            © {new Date().getFullYear()} Lumina Tech. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
