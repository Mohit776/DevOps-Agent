import mongoose, { Document, Model, Schema } from 'mongoose';

export interface IProduct extends Document {
  name: string;
  description: string;
  price: number;
  image: string;
  stock: number;
}

const productSchema = new Schema<IProduct>({
  name: { type: String, required: true },
  description: { type: String, required: true },
  price: { type: Number, required: true },
  image: { type: String, required: true },
  stock: { type: Number, required: true, default: 0 }
}, { timestamps: true });

export const Product: Model<IProduct> = mongoose.models.Product || mongoose.model('Product', productSchema);
