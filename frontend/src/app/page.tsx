"use client";

import { useState } from "react";
import { Zap, BarChart3, Calculator, Server, Activity } from "lucide-react";
import Header from "@/components/Header";
import FeeMonitorPanel from "@/components/FeeMonitorPanel";
import EvidencePanel from "@/components/EvidencePanel";
import WhatIfPanel from "@/components/WhatIfPanel";
import InfrastructurePanel from "@/components/InfrastructurePanel";
import ValuationContextPanel from "@/components/ValuationContextPanel";

const TABS = [
  { id: "fees", label: "Fees", icon: Zap },
  { id: "valuation", label: "Valuation", icon: Activity },
  { id: "evidence", label: "Evidence", icon: BarChart3 },
  { id: "project", label: "Projection", icon: Calculator },
  { id: "node", label: "Infrastructure", icon: Server },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabId>("fees");

  return (
    <>
      <Header />

      {/* Tab bar */}
      <div className="sticky top-0 z-20 border-b border-card-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <nav className="mx-auto flex w-full max-w-7xl px-4 sm:px-6 lg:px-8">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 border-b-2 px-5 py-3 text-sm font-medium transition-colors ${
                activeTab === id
                  ? "border-accent text-accent"
                  : "border-transparent text-muted hover:border-card-border hover:text-foreground"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
        <section className={activeTab === "fees" ? "" : "hidden"}>
          <FeeMonitorPanel />
        </section>

        <section className={activeTab === "valuation" ? "" : "hidden"}>
          <ValuationContextPanel />
        </section>

        <section className={activeTab === "evidence" ? "" : "hidden"}>
          <EvidencePanel />
        </section>

        <section className={activeTab === "project" ? "" : "hidden"}>
          <WhatIfPanel />
        </section>

        <section className={activeTab === "node" ? "" : "hidden"}>
          <InfrastructurePanel />
        </section>
      </main>

      <footer className="border-t border-card-border py-6 text-center text-xs text-muted">
        SteadyStack v0.2.0 — Fee-Aware DCA — Not financial advice
      </footer>
    </>
  );
}
