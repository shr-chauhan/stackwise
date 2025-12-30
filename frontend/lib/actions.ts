"use server";

import { signOut } from "@/lib/auth";
import { clearApiToken } from "@/lib/api";

export async function signOutAction() {
  // Clear API token (client-side, but called from server action)
  // The token will be cleared when the page reloads
  await signOut({ redirectTo: "/login" });
}


