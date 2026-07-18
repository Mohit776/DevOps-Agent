import mongoose from 'mongoose';
import bcrypt from 'bcryptjs';

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/ecommerce';

const users = [
  { name: 'Admin', email: 'admin@example.com', password: 'password', role: 'admin' },
  { name: 'User 1', email: 'user1@example.com', password: 'password', role: 'user' },
  { name: 'User 2', email: 'user2@example.com', password: 'password', role: 'user' },
  { name: 'User 3', email: 'user3@example.com', password: 'password', role: 'user' },
];

const products = Array.from({ length: 10 }).map((_, i) => ({
  name: `Product ${i + 1}`,
  description: `Description for product ${i + 1}`,
  price: (i + 1) * 10,
  image: `https://via.placeholder.com/150?text=Product+${i + 1}`,
  stock: 100,
}));

async function seed() {
  try {
    console.log('Connecting to database...');
    await mongoose.connect(MONGODB_URI);
    
    console.log('Clearing existing data...');
    await mongoose.connection.db?.dropDatabase();

    console.log('Seeding users...');
    for (const u of users) {
      const hashedPassword = await bcrypt.hash(u.password, 10);
      await mongoose.connection.collection('users').insertOne({
        ...u,
        password: hashedPassword,
        createdAt: new Date(),
        updatedAt: new Date()
      });
    }

    console.log('Seeding products...');
    await mongoose.connection.collection('products').insertMany(
      products.map(p => ({ ...p, createdAt: new Date(), updatedAt: new Date() }))
    );

    console.log('Database seeded successfully!');
    process.exit(0);
  } catch (error) {
    console.error('Seeding failed:', error);
    process.exit(1);
  }
}

seed();
