/**
 * Centralized backend configuration.
 * All server-side code should import BACKEND_URL from here
 * instead of duplicating `process.env.BACKEND_URL || "..."`.
 */
export const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8080";
