import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  /* config options here */
  // Silence workspace root inference warning by explicitly setting the root
  // used for output file tracing. Point this to the project root containing
  // your lockfile and node_modules for this app.
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
