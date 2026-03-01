"use client";

import Script from "next/script";

/**
 * Renders the GA4 gtag.js snippet when a measurement ID is configured.
 *
 * Environment variable flow:
 *   GA4_MEASUREMENT_ID (server-side)
 *     → next.config.ts `env` block
 *       → NEXT_PUBLIC_GA4_MEASUREMENT_ID (available in the browser bundle)
 *
 * When the env var is blank the component renders nothing, so GA4 is
 * completely absent in environments that haven't set the variable.
 *
 * `debug_mode` is always enabled since the app currently only runs locally.
 */
export function GoogleAnalytics() {
  const measurementId = process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID;

  if (!measurementId) {
    return null;
  }

  return (
    <>
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${measurementId}`}
        strategy="afterInteractive"
        onLoad={() =>
          console.log(`[GA4] gtag.js loaded successfully (${measurementId})`)
        }
        onError={() =>
          console.error(`[GA4] Failed to load gtag.js for ${measurementId}`)
        }
      />
      <Script id="ga4-init" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          window.gtag = function(){window.dataLayer.push(arguments);};
          window.gtag('js', new Date());
          window.gtag('config', '${measurementId}', {
            debug_mode: true
          });
          console.log('[GA4] Initialized and config sent for ${measurementId}');
        `}
      </Script>
    </>
  );
}
