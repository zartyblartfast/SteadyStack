"use client";

import { Bitcoin } from "lucide-react";

export default function Header() {
  return (
    <header className="border-b border-card-border bg-card">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-3">
            <Bitcoin className="h-8 w-8 text-accent" />
            <div>
              <h1 className="text-lg font-bold tracking-tight">SteadyStack</h1>
              <p className="text-xs text-muted">Bitcoin DCA Done Properly</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="rounded-full bg-accent/10 px-3 py-1 text-xs font-medium text-accent">
              Fee-Aware · Non-Custodial
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
