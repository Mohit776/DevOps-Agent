export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh]">
      <h1 className="text-4xl font-bold">404 - Not Found</h1>
      <p className="mt-4">The page you are looking for does not exist.</p>
      <a href="/" className="mt-6 text-blue-500 hover:underline">Return Home</a>
    </div>
  );
}
