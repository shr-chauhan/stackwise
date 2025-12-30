/**
 * Utility to sync user with backend after GitHub OAuth login
 */

import { auth } from "@/lib/auth";
import { api, setApiToken } from "@/lib/api";

/**
 * Sync current user with backend after GitHub login
 * Should be called after successful GitHub OAuth authentication
 * 
 * This function is non-blocking and will not throw errors.
 * It silently fails if the backend is unavailable.
 */
export async function syncUserWithBackend(): Promise<void> {
  try {
    const session = await auth();
    
    if (!session?.user) {
      // No session - nothing to sync
      return;
    }

    // Sync user with backend (with timeout handled in apiRequest)
    await api.syncUser({
      github_id: session.user.id || "",
      username: session.user.username || session.user.name || "",
      email: session.user.email || null,
      name: session.user.name || null,
      avatar_url: session.user.image || null,
    });
    
    // Only log success in development
    if (process.env.NODE_ENV === 'development') {
      console.log("User synced with backend successfully");
    }
  } catch (error) {
    // Silently fail - don't block the UI
    // The error is already logged by the API client
    // User can continue using the app, sync will retry on next page load
    if (process.env.NODE_ENV === 'development') {
      console.warn("User sync failed (non-blocking):", error instanceof Error ? error.message : "Unknown error");
    }
  }
}

