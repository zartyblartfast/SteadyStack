"use client";

import { useState } from "react";
import {
  Server,
  Shield,
  Cpu,
  Globe,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Zap,
  Lock,
  Users,
} from "lucide-react";

function Section({
  title,
  icon: Icon,
  children,
  defaultOpen = false,
}: {
  title: string;
  icon: typeof Server;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-xl border border-card-border bg-card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-card-border/10 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Icon className="h-5 w-5 text-accent" />
          <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">
            {title}
          </h3>
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 text-muted" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted" />
        )}
      </button>
      {open && <div className="px-5 pb-5">{children}</div>}
    </div>
  );
}

function InfoLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-accent hover:text-accent-dim transition-colors"
    >
      {label}
      <ExternalLink className="h-3 w-3" />
    </a>
  );
}

export default function InfrastructurePanel() {
  return (
    <div className="space-y-6">
      {/* Intro */}
      <div className="rounded-xl border border-card-border bg-card p-6">
        <h2 className="text-lg font-bold mb-2">Bitcoin Infrastructure</h2>
        <p className="text-sm text-muted leading-relaxed max-w-2xl">
          SteadyStack can route your DCA buys through Bitcoin infrastructure
          that supports decentralisation. You can use the provided node, or
          connect your own for full sovereignty.
        </p>
      </div>

      {/* How buys are routed */}
      <div className="rounded-xl border border-card-border bg-card p-5">
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted">
          How Your Buys Are Routed
        </h3>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-card-border p-4">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="h-5 w-5 text-accent" />
              <p className="font-medium text-sm">Standard Mode</p>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Buys are executed via your connected exchange with fee-optimal
              timing. SteadyStack monitors the mempool and advises when fees are
              low. No node required.
            </p>
          </div>
          <div className="rounded-lg border border-accent/30 p-4 bg-accent/5">
            <div className="flex items-center gap-2 mb-2">
              <Server className="h-5 w-5 text-accent" />
              <p className="font-medium text-sm">Provided Node</p>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Buys are broadcast through SteadyStack&apos;s Bitcoin Knots node
              with a DATUM gateway and BIP 110 template support. Your
              transactions contribute to decentralised block construction.
            </p>
          </div>
          <div className="rounded-lg border border-card-border p-4">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="h-5 w-5 text-accent" />
              <p className="font-medium text-sm">Your Own Node</p>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Advanced users can connect their own Bitcoin Knots node. Buys are
              broadcast through your infrastructure with your own block
              templates and policy preferences.
            </p>
          </div>
        </div>
      </div>

      {/* Bitcoin Knots */}
      <Section title="Bitcoin Knots" icon={Cpu} defaultOpen={true}>
        <div className="space-y-3 text-sm text-foreground/80 leading-relaxed">
          <p>
            <InfoLink href="https://bitcoinknots.org/" label="Bitcoin Knots" />{" "}
            is an alternative Bitcoin full node implementation maintained by Luke
            Dashjr. It includes all Bitcoin Core features plus additional
            enhancements:
          </p>
          <ul className="space-y-2 ml-4">
            <li className="flex gap-2">
              <span className="text-accent">•</span>
              <span>
                <strong>Enhanced mempool policies</strong> — more granular
                control over which transactions your node accepts and relays.
              </span>
            </li>
            <li className="flex gap-2">
              <span className="text-accent">•</span>
              <span>
                <strong>Better fee estimation</strong> — improved algorithms for
                estimating appropriate fee rates.
              </span>
            </li>
            <li className="flex gap-2">
              <span className="text-accent">•</span>
              <span>
                <strong>Transaction filtering</strong> — ability to filter spam
                transactions (Ordinals, Runes, etc.) from your node&apos;s
                mempool and block templates.
              </span>
            </li>
          </ul>
          <p>
            SteadyStack&apos;s provided node runs Bitcoin Knots, giving your
            transactions direct access to the Bitcoin network without relying on
            third-party broadcast services.
          </p>
        </div>
      </Section>

      {/* DATUM Gateway */}
      <Section title="DATUM Gateway & Block Templates" icon={Globe}>
        <div className="space-y-3 text-sm text-foreground/80 leading-relaxed">
          <p>
            <strong>DATUM</strong> (Decentralised Alternative Templates for
            Universal Mining) is a protocol that allows miners to construct their
            own block templates instead of relying on mining pool operators.
          </p>
          <div className="rounded-lg border border-accent/20 bg-accent/5 p-4 my-3">
            <h4 className="font-semibold text-accent text-xs uppercase tracking-wider mb-2">
              Why This Matters
            </h4>
            <p className="text-foreground/70">
              Today, a handful of large mining pools construct ~90% of Bitcoin
              blocks. This means pool operators decide which transactions get
              included. DATUM returns that power to individual miners and node
              operators, strengthening Bitcoin&apos;s censorship resistance.
            </p>
          </div>
          <p>
            When SteadyStack routes buys through a DATUM-enabled node, your
            transactions are included in block templates constructed by that
            node — not by a centralised pool. This supports:
          </p>
          <ul className="space-y-2 ml-4">
            <li className="flex gap-2">
              <Users className="h-4 w-4 text-accent mt-0.5 shrink-0" />
              <span>
                <strong>Decentralised block construction</strong> — more diverse
                block templates mean no single entity can censor transactions.
              </span>
            </li>
            <li className="flex gap-2">
              <Lock className="h-4 w-4 text-accent mt-0.5 shrink-0" />
              <span>
                <strong>Transaction privacy</strong> — your transaction is broadcast
                directly to miners, not through public mempool relay.
              </span>
            </li>
            <li className="flex gap-2">
              <Shield className="h-4 w-4 text-accent mt-0.5 shrink-0" />
              <span>
                <strong>Policy alignment</strong> — your node applies your
                preferred transaction filtering policies to the block template.
              </span>
            </li>
          </ul>
        </div>
      </Section>

      {/* BIP 110 */}
      <Section title="BIP 110 — Stratum v2 Template Distribution" icon={Shield}>
        <div className="space-y-3 text-sm text-foreground/80 leading-relaxed">
          <p>
            <strong>BIP 110</strong> defines a standardised protocol for
            distributing block templates between mining pools and miners. It is
            part of the broader{" "}
            <InfoLink
              href="https://www.stratumprotocol.org/"
              label="Stratum v2"
            />{" "}
            initiative.
          </p>
          <p>
            Under the current Stratum v1 protocol, mining pools send miners a
            pre-built block template. Miners have no say in which transactions
            are included. BIP 110 reverses this: miners (or their connected
            nodes) construct the template and the pool simply validates the
            proof-of-work.
          </p>
          <div className="grid gap-4 md:grid-cols-2 my-3">
            <div className="rounded-lg border border-danger/20 bg-danger/5 p-4">
              <h4 className="font-semibold text-danger text-xs uppercase tracking-wider mb-2">
                Without BIP 110
              </h4>
              <ul className="text-xs space-y-1 text-foreground/60">
                <li>Pool operator builds block template</li>
                <li>Pool decides which transactions to include</li>
                <li>Miner has no control over block content</li>
                <li>Centralised censorship risk</li>
              </ul>
            </div>
            <div className="rounded-lg border border-success/20 bg-success/5 p-4">
              <h4 className="font-semibold text-success text-xs uppercase tracking-wider mb-2">
                With BIP 110
              </h4>
              <ul className="text-xs space-y-1 text-foreground/60">
                <li>Miner&apos;s node builds block template</li>
                <li>Miner decides which transactions to include</li>
                <li>Pool only validates proof-of-work</li>
                <li>Decentralised, censorship-resistant</li>
              </ul>
            </div>
          </div>
          <p>
            SteadyStack supports BIP 110 signalling on its provided node and on
            user-connected nodes. This means your DCA transactions actively
            support the ecosystem&apos;s transition to decentralised mining.
          </p>
        </div>
      </Section>

      {/* Connect your own node */}
      <div className="rounded-xl border border-accent/20 bg-accent/5 p-6">
        <h3 className="font-bold text-accent mb-3 flex items-center gap-2">
          <Server className="h-5 w-5" />
          Connect Your Own Node
        </h3>
        <p className="text-sm text-foreground/80 leading-relaxed mb-4">
          Advanced users can connect their own Bitcoin Knots node to
          SteadyStack. This gives you full control over:
        </p>
        <ul className="text-sm text-foreground/80 space-y-1 mb-4">
          <li className="flex gap-2">
            <span className="text-accent">•</span>
            Transaction broadcasting and relay policy
          </li>
          <li className="flex gap-2">
            <span className="text-accent">•</span>
            Block template construction and filtering
          </li>
          <li className="flex gap-2">
            <span className="text-accent">•</span>
            Mempool fee estimation (from your own node&apos;s perspective)
          </li>
          <li className="flex gap-2">
            <span className="text-accent">•</span>
            DATUM gateway configuration and BIP 110 signalling
          </li>
        </ul>
        <p className="text-xs text-muted">
          Node connection is a post-MVP feature. Self-hosted setup
          documentation will be provided.
        </p>
      </div>
    </div>
  );
}
