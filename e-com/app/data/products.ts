export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  image: string;
  category: string;
}

export const products: Product[] = [
  {
    id: "1",
    name: "Aura Noise-Cancelling Headphones",
    description: "Experience pure silence and premium audio quality with our adaptive noise-cancelling technology.",
    price: 299.99,
    image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80",
    category: "Audio",
  },
  {
    id: "2",
    name: "Chronos Smartwatch Series X",
    description: "Stay connected and track your health with a sleek, minimalist design that fits any occasion.",
    price: 399.00,
    image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80",
    category: "Wearables",
  },
  {
    id: "3",
    name: "Lumina Mirrorless Camera",
    description: "Capture breathtaking photos and 4K videos with a compact body and interchangeable lenses.",
    price: 1299.50,
    image: "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80",
    category: "Photography",
  },
  {
    id: "4",
    name: "Nova Mechanical Keyboard",
    description: "Tactile feedback, customizable RGB, and an ergonomic layout for the ultimate typing experience.",
    price: 149.99,
    image: "https://images.unsplash.com/photo-1595225476474-87563907a212?w=800&q=80",
    category: "Accessories",
  },
  {
    id: "5",
    name: "Precision Wireless Mouse",
    description: "Ultra-fast response time and an ergonomic design to keep you productive all day.",
    price: 79.99,
    image: "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800&q=80",
    category: "Accessories",
  },
  {
    id: "6",
    name: "Echo Portable Smart Speaker",
    description: "Room-filling sound in a beautifully crafted, portable design. Take your music anywhere.",
    price: 199.99,
    image: "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800&q=80",
    category: "Audio",
  }
];
