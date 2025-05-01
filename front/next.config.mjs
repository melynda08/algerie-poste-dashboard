/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: {} // ✅ Correct
  }
  
};

export default nextConfig;
