"use client";

import React from "react";
import Link from "next/link";
import {
  MessageSquare,
  Users,
  Workflow,
  Zap,
  LogOut,
  LogIn,
} from "lucide-react";
import BrandLogo from "@/components/BrandLogo";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";

interface AppNavigationRailProps {
  currentTab: "chat" | "agents" | "workflows";
  totalTokensUsed?: number;
  onOpenUsage?: () => void;
  userEmail?: string | null;
  onSignOut?: () => void;
}

export default function AppNavigationRail({
  currentTab,
  totalTokensUsed = 0,
  onOpenUsage,
  userEmail,
  onSignOut,
}: AppNavigationRailProps) {
  return (
    <header className="h-12 border-b border-hairline bg-canvas/90 backdrop-blur-md px-3 sm:px-4 flex items-center justify-between sticky top-0 z-30 select-none font-sans">
      {/* Left: Swarm Brand Wordmark with Internet Logo */}
      <Link href="/" className="flex items-center gap-2 group">
        <BrandLogo size={22} showWordmark={true} versionBadge="v2.0" />
      </Link>

      {/* Center: 3-Pillar Segmented Switcher (Chat | Agents | Workflows) */}
      <nav className="flex items-center gap-0.5 p-0.5 rounded-pill bg-surface-1 border border-hairline shadow-xs">
        <Link
          href="/chat"
          className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-pill font-medium transition-colors ${
            currentTab === "chat"
              ? "bg-surface-2 text-ink border border-hairline-strong shadow-xs font-semibold"
              : "text-ink-subtle hover:text-ink"
          }`}
        >
          <MessageSquare size={12} className={currentTab === "chat" ? "text-linear-primary" : ""} />
          <span>Chat</span>
        </Link>

        <Link
          href="/agents"
          className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-pill font-medium transition-colors ${
            currentTab === "agents"
              ? "bg-surface-2 text-ink border border-hairline-strong shadow-xs font-semibold"
              : "text-ink-subtle hover:text-ink"
          }`}
        >
          <Users size={12} className={currentTab === "agents" ? "text-linear-primary" : ""} />
          <span>Agents</span>
        </Link>

        <Link
          href="/workflows"
          className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-pill font-medium transition-colors ${
            currentTab === "workflows"
              ? "bg-surface-2 text-ink border border-hairline-strong shadow-xs font-semibold"
              : "text-ink-subtle hover:text-ink"
          }`}
        >
          <Workflow size={12} className={currentTab === "workflows" ? "text-linear-primary" : ""} />
          <span>Workflows</span>
        </Link>
      </nav>

      {/* Right: Theme Toggle, Telemetry & User Account Menu */}
      <div className="flex items-center gap-1.5 sm:gap-2">
        {/* Light/Dark/Palette Mode Switcher */}
        <ThemeSwitcher compact={true} />

        {onOpenUsage && (
          <button
            type="button"
            onClick={onOpenUsage}
            className="flex items-center gap-1.5 px-2 py-1 bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong text-ink rounded-md text-xs font-mono transition-colors"
            title="View token telemetry"
          >
            <Zap size={11} className="text-linear-primary" />
            <span className="text-[11px]">{totalTokensUsed.toLocaleString()}</span>
            <span className="text-[9px] text-ink-subtle hidden md:inline">tks</span>
          </button>
        )}

        {userEmail ? (
          <div className="flex items-center gap-1.5 pl-1.5 border-l border-hairline">
            <div
              className="w-5 h-5 rounded-md bg-linear-primary text-white flex items-center justify-center font-medium text-[10px]"
              title={userEmail}
            >
              {userEmail[0].toUpperCase()}
            </div>
            {onSignOut && (
              <button
                type="button"
                onClick={onSignOut}
                className="p-1 rounded-md text-ink-subtle hover:text-red-400 hover:bg-surface-1 transition-colors"
                title="Sign out"
              >
                <LogOut size={12} />
              </button>
            )}
          </div>
        ) : (
          <Link
            href="/login"
            className="flex items-center gap-1 px-2 py-1 text-xs text-ink-muted hover:text-ink bg-surface-1 hover:bg-surface-2 border border-hairline rounded-md transition-colors"
          >
            <LogIn size={11} />
            <span className="hidden sm:inline">Sign In</span>
          </Link>
        )}
      </div>
    </header>
  );
}
