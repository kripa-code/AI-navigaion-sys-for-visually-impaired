/**
 * BlindBuddy — Backend Configuration
 * Update BACKEND_URL to your server's IP/hostname.
 */

// Replace with your server's local IP when running on a physical device
// e.g., 'http://192.168.1.42:8000'
export const BACKEND_URL = 'http://localhost:8000';
export const WS_URL = BACKEND_URL.replace('http', 'ws');
