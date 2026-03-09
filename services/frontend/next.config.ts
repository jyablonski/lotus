import type { NextConfig } from "next";

const ga4Id = process.env.GA4_MEASUREMENT_ID ?? "";
if (ga4Id) {
  console.log(`[GA4] Enabled with measurement ID: ${ga4Id}`);
} else {
  console.log("[GA4] Disabled — GA4_MEASUREMENT_ID is not set");
}

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "avatars.githubusercontent.com",
        pathname: "/**",
        port: "",
      },
    ],
  },
  env: {
    // Expose GA4 measurement ID to the browser.
    // Blank default: GA4 won't load when the var is unset.
    NEXT_PUBLIC_GA4_MEASUREMENT_ID: ga4Id,
  },
};

export default nextConfig;
