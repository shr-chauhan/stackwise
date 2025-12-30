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
    // Check if we already have a token
    const existingToken = getApiToken();
    if (existingToken) {
      setSynced(true);
      return;
    }

    // Only sync once
    if (synced) return;

    // Fetch session from NextAuth API route
    fetch('/api/auth/session')
      .then(res => {
        console.log('UserSync: Session response status:', res.status);
        return res.json();
      })
      .then(session => {
        console.log('UserSync: Full session data:', JSON.stringify(session, null, 2));
        
        if (session?.user && !synced) {
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
            setSynced(true);
            return;
          }
          
          if (!username || username === 'unknown') {
            console.error('UserSync: Missing username:', session.user);
            setSynced(true);
            return;
          }
          
          setSynced(true);
          
          // Sync user with backend - ensure all values are strings or null
          const userData = {
            github_id: String(githubId).trim(),
            username: String(username).trim(),
            email: session.user.email ? String(session.user.email).trim() : null,
            name: session.user.name ? String(session.user.name).trim() : null,
            avatar_url: session.user.image ? String(session.user.image).trim() : null,
          };
          
          console.log('UserSync: Sending user data to backend:', userData);
          
          api.syncUser(userData)
          .then((user) => {
            console.log('UserSync: ✅ Successfully synced user, token stored');
            // Dispatch custom event when sync completes
            window.dispatchEvent(new CustomEvent('user-synced'));
          })
          .catch((error) => {
            console.error("UserSync: ❌ Failed to sync user:", error);
            // Reset synced flag to allow retry
            setSynced(false);
          });
        } else if (!session?.user) {
          console.log('UserSync: No user in session');
          // No session, mark as synced to avoid retrying
          setSynced(true);
        }
      })
      .catch((error) => {
        console.error('UserSync: Failed to fetch session:', error);
        // Silently fail if session fetch fails
        setSynced(true); // Mark as synced to avoid infinite retries
      });
  }, [synced]);

  // This component doesn't render anything
  return null;
}

