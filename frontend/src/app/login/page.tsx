"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { Bot, ArrowLeft, ShieldCheck, Sparkles } from "lucide-react";
import { supabase } from "@/lib/supabase";

export default function Login() {
  const router = useRouter();

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
    <div className="min-h-screen bg-canvas text-ink flex flex-col justify-between font-sans selection:bg-linear-primary/25 selection:text-ink">
      {/* Top Bar */}
      <header className="w-full px-6 py-4 flex items-center justify-between max-w-5xl mx-auto">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-medium text-ink-subtle hover:text-ink transition-colors group"
        >
          <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
          <span>Back to Home</span>
        </Link>
        <span className="text-xs font-mono text-ink-tertiary">auth.swarm.internal</span>
      </header>

      {/* Main Login Card */}
      <main className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="max-w-md w-full rounded-lg border border-hairline bg-surface-1 p-8 shadow-card">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="w-10 h-10 rounded-md bg-surface-2 border border-hairline mx-auto flex items-center justify-center text-linear-primary mb-3">
              <Bot className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-medium tracking-card-title text-ink">
              Sign in to Swarm Intelligence
            </h1>
            <p className="text-xs text-ink-subtle mt-1.5 leading-relaxed tracking-body">
              Authenticate to synchronize your multi-agent conversation sessions, DAG pipelines,
              and live telemetry.
            </p>
          </div>

          {/* Supabase Auth UI with Linear Dark Design Styling */}
          <div className="auth-container">
            <Auth
              supabaseClient={supabase}
              theme="dark"
              appearance={{
                theme: ThemeSupa,
                variables: {
                  default: {
                    colors: {
                      brand: "#5e6ad2",
                      brandAccent: "#828fff",
                      brandButtonText: "#ffffff",
                      inputBackground: "#0f1011",
                      inputBorder: "#23252a",
                      inputBorderHover: "#34343a",
                      inputBorderFocus: "#5e69d1",
                      inputText: "#f7f8f8",
                      inputPlaceholder: "#8a8f98",
                      defaultButtonBackground: "#141516",
                      defaultButtonBorder: "#23252a",
                      defaultButtonText: "#f7f8f8",
                    },
                    radii: {
                      borderRadiusButton: "6px",
                      buttonBorderRadius: "6px",
                      inputBorderRadius: "6px",
                    },
                  },
                },
              }}
              providers={["github", "google"]}
              redirectTo={`${
                typeof window !== "undefined" ? window.location.origin : ""
              }/chat`}
            />
          </div>

          {/* Footer security badge */}
          <div className="mt-6 pt-4 border-t border-hairline flex items-center justify-between text-[11px] text-ink-subtle">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-semantic-success" />
              <span>Row-Level Security</span>
            </span>
            <span className="flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-linear-primary" />
              <span>Isolated Memory</span>
            </span>
          </div>
        </div>
      </main>

      {/* Subtle bottom note */}
      <footer className="py-4 text-center text-xs text-ink-tertiary">
        <span>Swarm Intelligence Platform • Protected by Supabase Auth</span>
      </footer>
    </div>
  );
}
