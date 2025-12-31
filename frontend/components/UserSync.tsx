"use client";

import { useEffect, useState } from "react";
import { api, getApiToken } from "@/lib/api";

/**
 * Client component that syncs user with backend after login
 * This runs on the client side to avoid server-side network issues
 * 
 * Gets session data from NextAuth API route and syncs with backend
 */
export function UserSync() {
  const [synced, setSynced] = useState(false);

  useEffect(() => {
    const performSync = async () => {
      // Fetch session from NextAuth API route
      try {
        const res = await fetch('/api/auth/session');
        console.log('UserSync: Session response status:', res.status);
        const session = await res.json();
        console.log('UserSync: Full session data:', JSON.stringify(session, null, 2));
        
        if (session?.user) {
          // Check what fields are available
          console.log('UserSync: User object:', {
            id: session.user.id,
            username: session.user.username,
            name: session.user.name,
            email: session.user.email,
            image: session.user.image
          });
          
          // Ensure we have required fields - github_id should be in user.id
          const githubId = session.user.id;
          const username = session.user.username || session.user.name || 'unknown';
          
          if (!githubId) {
            console.error('UserSync: Missing github_id (user.id):', session.user);
            return;
          }
          
          if (!username || username === 'unknown') {
            console.error('UserSync: Missing username:', session.user);
            return;
          }
          
          // Sync user with backend - ensure all values are strings or null
          const userData = {
            github_id: String(githubId).trim(),
            username: String(username).trim(),
            email: session.user.email ? String(session.user.email).trim() : null,
            name: session.user.name ? String(session.user.name).trim() : null,
            avatar_url: session.user.image ? String(session.user.image).trim() : null,
          };
          
          console.log('UserSync: Sending user data to backend:', userData);
          
          try {
            const user = await api.syncUser(userData);
            console.log('UserSync: ✅ Successfully synced user, token stored');
            // Dispatch custom event when sync completes
            window.dispatchEvent(new CustomEvent('user-synced'));
          } catch (error) {
            console.error("UserSync: ❌ Failed to sync user:", error);
          }
        } else {
          console.log('UserSync: No user in session');
        }
      } catch (error) {
        console.error('UserSync: Failed to fetch session:', error);
      }
    };

    // Check if we already have a token (but don't skip sync if token is invalid)
    const existingToken = getApiToken();
    if (existingToken && synced) {
      // Token exists and we've already synced, skip
      return;
    }

    // Listen for token-invalid event (triggered when API returns 401)
    const handleTokenInvalid = () => {
      console.log('UserSync: Token invalid event received, forcing re-sync');
      setSynced(false); // Reset synced flag to allow re-sync
      performSync();
    };

    window.addEventListener('token-invalid', handleTokenInvalid);

    // Perform initial sync if not already synced
    if (!synced) {
      performSync().then(() => {
        setSynced(true);
      });
    }

    return () => {
      window.removeEventListener('token-invalid', handleTokenInvalid);
    };
  }, [synced]);

  // This component doesn't render anything
  return null;
}

