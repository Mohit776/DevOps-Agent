import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { CartProvider } from "./context/CartContext";
import Navbar from "./components/Navbar";
import CartSidebar from "./components/CartSidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Lumina | Premium Tech Gear",
  description: "Shop the latest premium tech gear and accessories.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <body className={`${inter.className} min-h-full flex flex-col bg-black text-white`}>
        <CartProvider>
          <Navbar />
          <main className="flex-1 pt-16">
            {children}
          </main>
          <CartSidebar />
        </CartProvider>
      </body>
    </html>
  );
}
