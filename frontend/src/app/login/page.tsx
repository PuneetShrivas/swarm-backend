"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { Bot, ArrowLeft, ShieldCheck, Sparkles } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { useAppTheme } from "@/components/ThemeProvider";

export default function Login() {
  const router = useRouter();
  const { resolvedTheme, mounted } = useAppTheme();

  useEffect(() => {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        router.push("/chat");
      }
    });

    return () => subscription.unsubscribe();
  }, [router]);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between relative overflow-hidden transition-colors duration-300">
      {/* Background Grid & Glow */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--foreground)/0.03)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--foreground)/0.03)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />
      <div
        className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] rounded-full blur-[120px] pointer-events-none opacity-30"
        style={{
          background: "radial-gradient(circle, var(--glow-color) 0%, transparent 70%)",
        }}
      />

      {/* Top Bar */}
      <header className="relative z-10 w-full px-6 py-5 flex items-center justify-between max-w-6xl mx-auto">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span>Back to Home</span>
        </Link>
        <ThemeSwitcher />
      </header>

      {/* Main Login Card */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-4 py-8">
        <div className="max-w-md w-full rounded-2xl border border-border/80 bg-card/80 backdrop-blur-xl p-8 sm:p-10 shadow-card">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/25 mx-auto flex items-center justify-center text-primary mb-4 shadow-subtle">
              <Bot className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Sign in to Swarm Intelligence
            </h1>
            <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
              Authenticate to synchronize your multi-agent conversation sessions, tree branches,
              and live telemetry across devices.
            </p>
          </div>

          {/* Supabase Auth UI with Active Theme Mode */}
          <div className="auth-container">
            {mounted && (
              <Auth
                supabaseClient={supabase}
                theme={resolvedTheme === "dark" ? "dark" : "default"}
                appearance={{
                  theme: ThemeSupa,
                  variables: {
                    default: {
                      colors: {
                        brand: "hsl(var(--primary))",
                        brandAccent: "hsl(var(--primary))",
                        brandButtonText: "hsl(var(--primary-foreground))",
                        inputBackground: "hsl(var(--card))",
                        inputBorder: "hsl(var(--border))",
                        inputBorderHover: "hsl(var(--primary))",
                        inputBorderFocus: "hsl(var(--primary))",
                        inputText: "hsl(var(--foreground))",
                        inputPlaceholder: "hsl(var(--muted-foreground))",
                        defaultButtonBackground: "hsl(var(--card))",
                        defaultButtonBorder: "hsl(var(--border))",
                        defaultButtonText: "hsl(var(--foreground))",
                      },
                      radii: {
                        borderRadiusButton: "0.5rem",
                        buttonBorderRadius: "0.5rem",
                        inputBorderRadius: "0.5rem",
                      },
                    },
                  },
                }}
                providers={["github", "google"]}
                redirectTo={`${
                  typeof window !== "undefined" ? window.location.origin : ""
                }/chat`}
              />
            )}
          </div>

          {/* Footer security badge */}
          <div className="mt-8 pt-4 border-t border-border/60 flex items-center justify-between text-[11px] text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              <span>Row-Level Security</span>
            </span>
            <span className="flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-primary" />
              <span>Session Isolation</span>
            </span>
          </div>
        </div>
      </main>

      {/* Subtle bottom note */}
      <footer className="relative z-10 py-4 text-center text-xs text-muted-foreground">
        <span>Swarm Intelligence Platform • Protected by Supabase Auth</span>
      </footer>
    </div>
  );
}
