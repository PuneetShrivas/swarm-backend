import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://swarm-backend-fronted.vercel.app"),
  title: {
    default: "Swarm — Autonomous Multi-Agent Orchestration & Workflow Studio",
    template: "%s | Swarm",
  },
  description:
    "Production-grade multi-agent swarm platform with autonomous DAG workflow builder, dynamic dialogue tree branching, AST-sandboxed custom tools, live Perplexity search, and sub-millisecond execution telemetry.",
  keywords: [
    "AI Agent Swarm",
    "Multi-Agent Systems",
    "Autonomous Workflows",
    "DAG Studio",
    "Dialogue Tree Branching",
    "Perplexity Sonar",
    "FastAPI AI",
    "Next.js AI Platform",
    "Agentic Workflows",
  ],
  authors: [{ name: "Swarm Platform Engineering" }],
  creator: "Swarm Platform Engineering",
  publisher: "Swarm",
  icons: {
    icon: "/swarm-logo.png",
    shortcut: "/swarm-logo.png",
    apple: "/swarm-logo.png",
  },
  openGraph: {
    title: "Swarm — Autonomous Multi-Agent Orchestration & Workflow Studio",
    description:
      "Design, orchestrate, and deploy production-grade multi-agent swarms with visual DAG pipelines, live Perplexity web synthesis, and real-time execution telemetry.",
    url: "https://swarm-backend-fronted.vercel.app",
    siteName: "Swarm",
    images: [
      {
        url: "/swarm-logo.png",
        width: 512,
        height: 512,
        alt: "Swarm Platform Logo",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Swarm — Autonomous Multi-Agent Orchestration & Workflow Studio",
    description:
      "Design, orchestrate, and deploy production-grade multi-agent swarms with visual DAG pipelines.",
    images: ["/swarm-logo.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased min-h-screen bg-background text-foreground`}
      >
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
