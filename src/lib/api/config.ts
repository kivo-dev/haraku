/** Base URL of the backend. Empty = no backend yet, the built-in sample data is used. */
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");
export const apiEnabled = Boolean(API_BASE);
