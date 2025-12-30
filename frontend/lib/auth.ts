/**
 * NextAuth configuration for GitHub OAuth
 */

import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";

// Validate required environment variables
if (!process.env.GITHUB_CLIENT_ID) {
  console.warn("⚠️  GITHUB_CLIENT_ID is not set. GitHub OAuth will not work.");
}

if (!process.env.GITHUB_CLIENT_SECRET) {
  console.warn("⚠️  GITHUB_CLIENT_SECRET is not set. GitHub OAuth will not work.");
}

if (!process.env.AUTH_SECRET) {
  console.warn("⚠️  AUTH_SECRET is not set. Sessions will not be secure.");
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  // Trust the host header (needed for Next.js in development)
  trustHost: true,
  providers: [
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID || "",
      clientSecret: process.env.GITHUB_CLIENT_SECRET || "",
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      // Persist the OAuth access_token and user info to the token right after signin
      if (account) {
        token.accessToken = account.access_token;
        token.providerAccountId = account.providerAccountId;
      }
      if (profile) {
        token.githubId = String(profile.id);  // Ensure it's a string
        token.username = profile.login;
        token.email = profile.email;
      }
      return token;
    },
    async session({ session, token }) {
      // Send properties to the client
      if (session.user) {
        session.user.id = token.githubId as string;
        session.user.username = token.username as string;
        session.user.email = token.email as string;
      }
      return session;
    },
  },
  pages: {
    signIn: '/login',
  },
});

// Extend NextAuth types
declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
      username?: string;
    };
  }
}


