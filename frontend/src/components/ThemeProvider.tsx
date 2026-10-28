"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { ThemeProvider as NextThemesProvider, useTheme } from "next-themes";

export type ThemeMode = "light" | "dark" | "system";
export type ThemePalette = "slate" | "nebula" | "emerald" | "amber" | "frost";

export interface PaletteOption {
  id: ThemePalette;
  name: string;
  description: string;
  color: string; // Preview dot color
  accentGlow: string;
}

export const PALETTES: PaletteOption[] = [
  {
    id: "slate",
    name: "Modern Slate",
    description: "Monochrome minimalism & graphite accents",
    color: "#64748b",
    accentGlow: "rgba(99, 102, 241, 0.25)",
  },
  {
    id: "nebula",
    name: "Violet Nebula",
    description: "Cyber indigo & iridescent electric violet",
    color: "#8b5cf6",
    accentGlow: "rgba(139, 92, 246, 0.35)",
  },
  {
    id: "emerald",
    name: "Matrix Emerald",
    description: "Sleek obsidian & vibrant terminal green",
    color: "#10b981",
    accentGlow: "rgba(16, 185, 129, 0.35)",
  },
  {
    id: "amber",
    name: "Solar Amber",
    description: "Warm espresso charcoal & luxe amber gold",
    color: "#f59e0b",
    accentGlow: "rgba(245, 158, 11, 0.35)",
  },
  {
    id: "frost",
    name: "Glacier Frost",
    description: "Abyssal arctic navy & glowing cyan ice",
    color: "#0ea5e9",
    accentGlow: "rgba(14, 165, 233, 0.35)",
  },
];

interface AppThemeContextType {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  palette: ThemePalette;
  setPalette: (palette: ThemePalette) => void;
  resolvedTheme: "light" | "dark";
  mounted: boolean;
}

const AppThemeContext = createContext<AppThemeContextType | undefined>(undefined);

function PaletteManager({ children }: { children: React.ReactNode }) {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [palette, setPaletteState] = useState<ThemePalette>("slate");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    try {
      const savedPalette = localStorage.getItem("swarm-palette") as ThemePalette | null;
      if (
        savedPalette &&
        ["slate", "nebula", "emerald", "amber", "frost"].includes(savedPalette)
      ) {
        setPaletteState(savedPalette);
        document.documentElement.setAttribute("data-palette", savedPalette);
      } else {
        document.documentElement.setAttribute("data-palette", "slate");
      }
    } catch {
      // LocalStorage unavailable
      document.documentElement.setAttribute("data-palette", "slate");
    }
    setMounted(true);
  }, []);

  const setPalette = (newPalette: ThemePalette) => {
    setPaletteState(newPalette);
    try {
      localStorage.setItem("swarm-palette", newPalette);
    } catch {
      // Ignore storage errors
    }
    document.documentElement.setAttribute("data-palette", newPalette);
  };

  const handleSetMode = (mode: ThemeMode) => {
    setTheme(mode);
  };

  return (
    <AppThemeContext.Provider
      value={{
        mode: (theme as ThemeMode) || "system",
        setMode: handleSetMode,
        palette,
        setPalette,
        resolvedTheme: (resolvedTheme as "light" | "dark") || "dark",
        mounted,
      }}
    >
      {children}
    </AppThemeContext.Provider>
  );
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      disableTransitionOnChange={false}
    >
      <PaletteManager>{children}</PaletteManager>
    </NextThemesProvider>
  );
}

export function useAppTheme() {
  const context = useContext(AppThemeContext);
  if (!context) {
    throw new Error("useAppTheme must be used within a ThemeProvider");
  }
  return context;
}
