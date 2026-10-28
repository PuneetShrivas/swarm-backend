import { createClient, Session } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://xyzcompany.supabase.co';
const supabaseAnonKey =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
  'public-anon-key';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

/**
 * Retrieves the current active Supabase session.
 */
export async function getSession(): Promise<Session | null> {
  try {
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error) {
      console.warn("Supabase getSession notice:", error);
      return null;
    }
    return session;
  } catch (err) {
    console.warn("Could not retrieve Supabase session:", err);
    return null;
  }
}

/**
 * Retrieves the active access token string if logged in.
 */
export async function getAuthToken(): Promise<string | null> {
  const session = await getSession();
  return session?.access_token || null;
}

/**
 * Returns authorization headers with the current Supabase JWT token.
 * If logged in, sends `Bearer <jwt>`. In local development fallback without
 * session, sends `Bearer dev-user-local` so local APIs operate seamlessly.
 */
export async function getAuthHeaders(): Promise<Record<string, string>> {
  const token = await getAuthToken();
  if (token) {
    return {
      Authorization: `Bearer ${token}`,
    };
  }
  return {
    Authorization: `Bearer dev-user-local`,
  };
}
