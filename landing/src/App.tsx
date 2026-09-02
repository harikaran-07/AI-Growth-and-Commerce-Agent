import { useState } from "react";

const NAV_LINKS = ["Platform", "Solutions", "Pricing", "Developers", "Enterprise"];

const LOGOS = ["Stripe", "Shopify", "Salesforce", "HubSpot", "Adobe", "Twilio"];

const FEATURES = [
  {
    tag: "AUTONOMOUS AGENTS",
    title: "Agents that act,\nnot just advise",
    body: "Deploy specialized AI agents that execute multi-step growth workflows autonomously — from lead qualification to checkout recovery — without human intervention.",
    stat: "94%",
    statLabel: "task completion rate",
    icon: (
      <svg viewBox="0 0 40 40" fill="none" className="w-10 h-10">
        <circle cx="20" cy="20" r="18" stroke="#00d4a8" strokeWidth="1.5" />
        <path d="M13 20l5 5 9-10" stroke="#00d4a8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    tag: "REVENUE INTELLIGENCE",
    title: "Predict revenue\nbefore it happens",
    body: "Real-time pipeline analysis with causal models. Surface risks, accelerate deals, and optimize pricing based on behavioral signals across your entire customer base.",
    stat: "3.4×",
    statLabel: "forecast accuracy lift",
    icon: (
      <svg viewBox="0 0 40 40" fill="none" className="w-10 h-10">
        <polyline points="6,32 14,20 22,26 34,10" stroke="#00d4a8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="34" cy="10" r="3" fill="#00d4a8" />
      </svg>
    ),
  },
  {
    tag: "COMMERCE AUTOMATION",
    title: "Personalize every\ncommerce touchpoint",
    body: "Dynamic product recommendations, cart abandonment re-engagement, and conversion-optimized landing pages — all orchestrated by agents tuned to your catalog and customers.",
    stat: "41%",
    statLabel: "average GMV increase",
    icon: (
      <svg viewBox="0 0 40 40" fill="none" className="w-10 h-10">
        <rect x="8" y="14" width="24" height="18" rx="2" stroke="#00d4a8" strokeWidth="1.5" />
        <path d="M15 14v-3a5 5 0 0110 0v3" stroke="#00d4a8" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="20" cy="23" r="2" fill="#00d4a8" />
      </svg>
    ),
  },
  {
    tag: "GROWTH ORCHESTRATION",
    title: "One platform,\nevery growth lever",
    body: "Connect acquisition, activation, retention, and expansion into a unified agent layer. Eliminate silos between marketing, product, and sales with shared intelligence.",
    stat: "2.1×",
    statLabel: "pipeline velocity",
    icon: (
      <svg viewBox="0 0 40 40" fill="none" className="w-10 h-10">
        <circle cx="10" cy="20" r="4" stroke="#00d4a8" strokeWidth="1.5" />
        <circle cx="30" cy="10" r="4" stroke="#00d4a8" strokeWidth="1.5" />
        <circle cx="30" cy="30" r="4" stroke="#00d4a8" strokeWidth="1.5" />
        <line x1="14" y1="18" x2="26" y2="12" stroke="#00d4a8" strokeWidth="1.2" />
        <line x1="14" y1="22" x2="26" y2="28" stroke="#00d4a8" strokeWidth="1.2" />
      </svg>
    ),
  },
];

const STEPS = [
  {
    num: "01",
    title: "Connect your stack",
    body: "Integrate with your CRM, data warehouse, commerce platform, and marketing tools in minutes via native connectors or our unified API.",
  },
  {
    num: "02",
    title: "Deploy your agents",
    body: "Choose from a library of pre-built agent templates or configure custom agents to match your specific growth motions and business logic.",
  },
  {
    num: "03",
    title: "Measure compound returns",
    body: "Track agent-attributed revenue, experiment with strategies, and let agents self-optimize based on outcomes — not assumptions.",
  },
];

const TESTIMONIALS = [
  {
    quote: "We replaced five point solutions with Axon's agent layer. Our sales cycle compressed by 38% in the first quarter.",
    name: "Sofia Marchetti",
    role: "CRO, Lattice Commerce",
    avatar: "SM",
  },
  {
    quote: "The revenue intelligence has fundamentally changed how our board thinks about predictability. We've hit forecast within 3% for six consecutive quarters.",
    name: "Daniel Osei",
    role: "VP Revenue, Kova Systems",
    avatar: "DO",
  },
  {
    quote: "Autonomous cart recovery alone paid for the entire platform in week two. The compound effects on LTV are still compounding.",
    name: "Priya Nambiar",
    role: "Head of Growth, Merchi",
    avatar: "PN",
  },
];

const PLANS = [
  {
    name: "Startup",
    price: "$490",
    period: "/mo",
    desc: "For growth-stage teams proving the model.",
    features: ["3 active agents", "500K events/mo", "Core commerce connectors", "Email & chat support", "Standard analytics"],
    cta: "Start free trial",
    highlight: false,
  },
  {
    name: "Growth",
    price: "$1,890",
    period: "/mo",
    desc: "For scaling teams compounding revenue.",
    features: ["15 active agents", "5M events/mo", "All platform connectors", "Revenue intelligence suite", "Dedicated CSM", "Custom agent templates"],
    cta: "Start free trial",
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    desc: "For organizations with complex, global scale.",
    features: ["Unlimited agents", "Unlimited events", "Private cloud deployment", "SSO & RBAC", "SLA guarantees", "On-site onboarding"],
    cta: "Contact sales",
    highlight: false,
  },
];

const METRICS = [
  { value: "$4.2B", label: "Agent-attributed GMV" },
  { value: "12,400+", label: "Agents deployed globally" },
  { value: "99.97%", label: "Platform uptime SLA" },
  { value: "180ms", label: "Median agent response time" },
];

function MiniChart() {
  const points = [28, 35, 30, 45, 42, 55, 60, 52, 68, 74, 70, 85, 90, 88, 96];
  const max = 100;
  const w = 320;
  const h = 90;
  const pts = points
    .map((v, i) => `${(i / (points.length - 1)) * w},${h - (v / max) * h}`)
    .join(" ");
  const fill =
    points
      .map((v, i) => `${(i / (points.length - 1)) * w},${h - (v / max) * h}`)
      .join(" ") + ` ${w},${h} 0,${h}`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full" preserveAspectRatio="none">
      <defs>
        <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#00d4a8" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#00d4a8" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={fill} fill="url(#chartGrad)" />
      <polyline points={pts} fill="none" stroke="#00d4a8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function App() {
  const [activePlan, setActivePlan] = useState(1);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [billingAnnual, setBillingAnnual] = useState(true);

  return (
    <div className="min-h-full bg-[#070b14] text-[#e8eaf0] overflow-x-hidden">
      {/* NAV */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/[0.06] bg-[#070b14]/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-[#00d4a8] flex items-center justify-center">
              <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
                <path d="M10 3l7 4v6l-7 4-7-4V7l7-4z" stroke="#070b14" strokeWidth="1.5" strokeLinejoin="round" />
                <circle cx="10" cy="10" r="2" fill="#070b14" />
              </svg>
            </div>
            <span className="font-semibold tracking-tight text-[#e8eaf0]" style={{ fontFamily: "Instrument Sans, sans-serif" }}>
              Axon<span className="text-[#00d4a8]">AI</span>
            </span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map((l) => (
              <a key={l} href="#" className="text-sm text-[#8895a7] hover:text-[#e8eaf0] transition-colors">
                {l}
              </a>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-3">
            <a href="#" className="text-sm text-[#8895a7] hover:text-[#e8eaf0] transition-colors px-3 py-1.5">
              Sign in
            </a>
            <a
              href="#"
              className="text-sm font-medium bg-[#00d4a8] text-[#070b14] px-4 py-2 rounded hover:bg-[#00bfa0] transition-colors"
            >
              Get started
            </a>
          </div>

          <button
            className="md:hidden text-[#8895a7] hover:text-[#e8eaf0]"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5">
              <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {mobileOpen && (
          <div className="md:hidden border-t border-white/[0.06] bg-[#070b14] px-6 py-4 flex flex-col gap-4">
            {NAV_LINKS.map((l) => (
              <a key={l} href="#" className="text-sm text-[#8895a7]">
                {l}
              </a>
            ))}
            <a href="#" className="text-sm font-medium bg-[#00d4a8] text-[#070b14] px-4 py-2 rounded text-center mt-2">
              Get started
            </a>
          </div>
        )}
      </nav>

      {/* HERO */}
      <section className="relative pt-32 pb-24 px-6 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-[#00d4a8]/[0.04] rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-20 right-[15%] w-72 h-72 bg-[#3b5bdb]/[0.06] rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto">
          <div className="mb-6 inline-flex items-center gap-2 border border-[#00d4a8]/20 bg-[#00d4a8]/[0.05] rounded-full px-4 py-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00d4a8] animate-pulse" />
            <span className="font-mono-data text-xs text-[#00d4a8] tracking-widest uppercase">
              Now in general availability
            </span>
          </div>

          <div className="grid lg:grid-cols-[1fr_420px] gap-16 items-start">
            <div>
              <h1
                className="font-serif text-5xl md:text-6xl lg:text-7xl leading-[1.05] tracking-tight mb-6"
                style={{ fontFamily: "DM Serif Display, serif" }}
              >
                AI agents built
                <br />
                <span className="italic text-[#00d4a8]">for revenue,</span>
                <br />
                not experiments.
              </h1>
              <p className="text-lg text-[#8895a7] max-w-lg leading-relaxed mb-10">
                Axon deploys autonomous agents across your growth and commerce stack — qualifying leads,
                recovering carts, optimizing pricing, and compounding revenue without manual intervention.
              </p>
              <div className="flex flex-wrap gap-3">
                <a
                  href="#"
                  className="inline-flex items-center gap-2 bg-[#00d4a8] text-[#070b14] font-semibold text-sm px-6 py-3 rounded hover:bg-[#00bfa0] transition-colors"
                >
                  Start free trial
                  <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4">
                    <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </a>
                <a
                  href="#"
                  className="inline-flex items-center gap-2 border border-white/10 text-[#e8eaf0] text-sm px-6 py-3 rounded hover:border-white/20 transition-colors"
                >
                  Watch demo
                </a>
              </div>
              <p className="mt-4 text-xs text-[#4a5568]">No credit card required · SOC 2 Type II certified · GDPR compliant</p>
            </div>

            <div className="bg-[#0d1525] border border-white/[0.08] rounded-xl overflow-hidden shadow-2xl shadow-black/40">
              <div className="border-b border-white/[0.06] px-4 py-3 flex items-center gap-2">
                <div className="flex gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-white/10" />
                  <span className="w-3 h-3 rounded-full bg-white/10" />
                  <span className="w-3 h-3 rounded-full bg-white/10" />
                </div>
                <span className="font-mono-data text-xs text-[#4a5568] ml-2">revenue-dashboard</span>
              </div>
              <div className="p-5">
                <div className="flex items-start justify-between mb-1">
                  <div>
                    <p className="font-mono-data text-xs text-[#4a5568] uppercase tracking-wider mb-1">
                      Agent-attributed GMV
                    </p>
                    <p
                      className="font-serif text-3xl text-[#e8eaf0]"
                      style={{ fontFamily: "DM Serif Display, serif" }}
                    >
                      $847,203
                    </p>
                  </div>
                  <span className="font-mono-data text-xs bg-[#00d4a8]/10 text-[#00d4a8] px-2 py-1 rounded">
                    ↑ 23.4%
                  </span>
                </div>
                <p className="font-mono-data text-xs text-[#4a5568] mb-4">vs. last 30 days</p>
                <div className="h-20">
                  <MiniChart />
                </div>
                <div className="mt-4 grid grid-cols-3 gap-3 pt-4 border-t border-white/[0.06]">
                  {[
                    { l: "Agents active", v: "12" },
                    { l: "Conversions", v: "3,841" },
                    { l: "Avg. order", v: "$220" },
                  ].map((m) => (
                    <div key={m.l}>
                      <p className="font-mono-data text-[10px] text-[#4a5568] mb-0.5">{m.l}</p>
                      <p className="font-mono-data text-sm text-[#e8eaf0] font-medium">{m.v}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t border-white/[0.06]">
                  <p className="font-mono-data text-[10px] text-[#4a5568] uppercase tracking-wider mb-3">
                    Agent activity
                  </p>
                  {[
                    {
                      agent: "cart-recovery-01",
                      action: "Re-engaged 14 abandoned carts",
                      time: "2m ago",
                      status: "success",
                    },
                    {
                      agent: "pricing-optimizer",
                      action: "Adjusted 6 SKU prices",
                      time: "8m ago",
                      status: "success",
                    },
                    {
                      agent: "lead-qualifier",
                      action: "Scored 47 inbound leads",
                      time: "15m ago",
                      status: "running",
                    },
                  ].map((item) => (
                    <div key={item.agent} className="flex items-start gap-2 mb-2.5">
                      <span
                        className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                          item.status === "running"
                            ? "bg-[#fbbf24] animate-pulse"
                            : "bg-[#00d4a8]"
                        }`}
                      />
                      <div className="min-w-0">
                        <p className="font-mono-data text-[10px] text-[#00d4a8]">{item.agent}</p>
                        <p className="text-xs text-[#8895a7] truncate">{item.action}</p>
                      </div>
                      <span className="font-mono-data text-[10px] text-[#4a5568] flex-shrink-0 ml-auto">
                        {item.time}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* LOGOS */}
      <section className="py-12 border-y border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-6">
          <p className="font-mono-data text-xs text-[#4a5568] uppercase tracking-widest text-center mb-8">
            Trusted by teams at
          </p>
          <div className="flex flex-wrap justify-center items-center gap-8 md:gap-12">
            {LOGOS.map((l) => (
              <span
                key={l}
                className="font-semibold text-[#2d3748] text-lg tracking-tight hover:text-[#4a5568] transition-colors cursor-default"
              >
                {l}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* METRICS */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/[0.06] border border-white/[0.06] rounded-xl overflow-hidden">
            {METRICS.map((m) => (
              <div key={m.label} className="bg-[#070b14] p-8">
                <p
                  className="font-serif text-4xl md:text-5xl text-[#e8eaf0] mb-2"
                  style={{ fontFamily: "DM Serif Display, serif" }}
                >
                  {m.value}
                </p>
                <p className="font-mono-data text-xs text-[#4a5568] uppercase tracking-wider">{m.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-14">
            <p className="font-mono-data text-xs text-[#00d4a8] uppercase tracking-widest mb-4">
              Platform capabilities
            </p>
            <h2
              className="font-serif text-4xl md:text-5xl leading-tight max-w-2xl"
              style={{ fontFamily: "DM Serif Display, serif" }}
            >
              Everything growth teams need. Nothing they don't.
            </h2>
          </div>
          <div className="grid md:grid-cols-2 gap-px bg-white/[0.06] border border-white/[0.06] rounded-xl overflow-hidden">
            {FEATURES.map((f, i) => (
              <div
                key={f.tag}
                className={`bg-[#070b14] p-8 md:p-10 flex flex-col gap-6 group hover:bg-[#0d1525] transition-colors ${
                  i === 0 ? "rounded-tl-xl" : ""
                } ${i === 1 ? "rounded-tr-xl" : ""} ${i === 2 ? "rounded-bl-xl" : ""} ${
                  i === 3 ? "rounded-br-xl" : ""
                }`}
              >
                <div className="flex items-start justify-between">
                  {f.icon}
                  <div className="text-right">
                    <p
                      className="font-serif text-3xl text-[#00d4a8]"
                      style={{ fontFamily: "DM Serif Display, serif" }}
                    >
                      {f.stat}
                    </p>
                    <p className="font-mono-data text-[10px] text-[#4a5568] uppercase tracking-wider">
                      {f.statLabel}
                    </p>
                  </div>
                </div>
                <div>
                  <p className="font-mono-data text-[10px] text-[#00d4a8] uppercase tracking-widest mb-3">
                    {f.tag}
                  </p>
                  <h3
                    className="font-serif text-2xl leading-snug mb-3 whitespace-pre-line"
                    style={{ fontFamily: "DM Serif Display, serif" }}
                  >
                    {f.title}
                  </h3>
                  <p className="text-sm text-[#8895a7] leading-relaxed">{f.body}</p>
                </div>
                <a
                  href="#"
                  className="inline-flex items-center gap-1.5 text-sm text-[#00d4a8] group-hover:gap-3 transition-all"
                >
                  Learn more
                  <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4">
                    <path
                      d="M3 8h10M9 4l4 4-4 4"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="py-20 px-6 border-t border-white/[0.06]">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-[1fr_1.4fr] gap-20 items-start">
            <div>
              <p className="font-mono-data text-xs text-[#00d4a8] uppercase tracking-widest mb-4">
                How it works
              </p>
              <h2
                className="font-serif text-4xl md:text-5xl leading-tight mb-6"
                style={{ fontFamily: "DM Serif Display, serif" }}
              >
                Live in days,
                <br />
                <span className="italic">compounding forever.</span>
              </h2>
              <p className="text-[#8895a7] text-sm leading-relaxed">
                Most teams are live with their first agents within 72 hours. No ML expertise required —
                connect your stack, configure your agents, and let compound returns begin.
              </p>
            </div>
            <div className="flex flex-col gap-0">
              {STEPS.map((s, i) => (
                <div
                  key={s.num}
                  className={`flex gap-8 py-8 ${i < STEPS.length - 1 ? "border-b border-white/[0.06]" : ""}`}
                >
                  <div className="flex-shrink-0">
                    <span
                      className="font-serif text-5xl text-white/10"
                      style={{ fontFamily: "DM Serif Display, serif" }}
                    >
                      {s.num}
                    </span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-[#e8eaf0] mb-2">{s.title}</h3>
                    <p className="text-sm text-[#8895a7] leading-relaxed">{s.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="py-20 px-6 border-t border-white/[0.06]">
        <div className="max-w-7xl mx-auto">
          <div className="mb-14 flex items-end justify-between flex-wrap gap-4">
            <div>
              <p className="font-mono-data text-xs text-[#00d4a8] uppercase tracking-widest mb-4">
                Customer stories
              </p>
              <h2
                className="font-serif text-4xl md:text-5xl leading-tight"
                style={{ fontFamily: "DM Serif Display, serif" }}
              >
                Results that compound.
              </h2>
            </div>
            <a
              href="#"
              className="text-sm text-[#8895a7] hover:text-[#e8eaf0] transition-colors underline underline-offset-4"
            >
              Read all case studies →
            </a>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((t) => (
              <div
                key={t.name}
                className="bg-[#0d1525] border border-white/[0.08] rounded-xl p-8 flex flex-col gap-6 hover:border-[#00d4a8]/20 transition-colors"
              >
                <div className="flex gap-1">
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} viewBox="0 0 12 12" className="w-3 h-3">
                      <polygon
                        points="6,1 7.5,4.5 11,4.5 8.3,7 9.3,11 6,8.5 2.7,11 3.7,7 1,4.5 4.5,4.5"
                        fill="#00d4a8"
                      />
                    </svg>
                  ))}
                </div>
                <p className="text-[#c4c9d4] text-sm leading-relaxed flex-1">"{t.quote}"</p>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-[#1a2640] flex items-center justify-center font-mono-data text-xs text-[#00d4a8]">
                    {t.avatar}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-[#e8eaf0]">{t.name}</p>
                    <p className="font-mono-data text-[10px] text-[#4a5568]">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section className="py-20 px-6 border-t border-white/[0.06]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <p className="font-mono-data text-xs text-[#00d4a8] uppercase tracking-widest mb-4">Pricing</p>
            <h2
              className="font-serif text-4xl md:text-5xl leading-tight mb-6"
              style={{ fontFamily: "DM Serif Display, serif" }}
            >
              Aligned with your growth.
            </h2>
            <div className="inline-flex items-center gap-3 bg-[#0d1525] border border-white/[0.08] rounded-full p-1">
              <button
                onClick={() => setBillingAnnual(false)}
                className={`px-4 py-1.5 rounded-full text-sm transition-colors ${
                  !billingAnnual ? "bg-[#1a2640] text-[#e8eaf0]" : "text-[#4a5568]"
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingAnnual(true)}
                className={`px-4 py-1.5 rounded-full text-sm transition-colors ${
                  billingAnnual ? "bg-[#1a2640] text-[#e8eaf0]" : "text-[#4a5568]"
                }`}
              >
                Annual
                <span className="ml-1.5 font-mono-data text-[10px] text-[#00d4a8]">–20%</span>
              </button>
            </div>
          </div>
          <div className="grid md:grid-cols-3 gap-6 items-start">
            {PLANS.map((plan, i) => (
              <div
                key={plan.name}
                onClick={() => setActivePlan(i)}
                className={`relative rounded-xl border p-8 cursor-pointer transition-all ${
                  plan.highlight
                    ? "border-[#00d4a8]/40 bg-[#0d1525] shadow-lg shadow-[#00d4a8]/5"
                    : "border-white/[0.08] bg-[#0d1525] hover:border-white/20"
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#00d4a8] text-[#070b14] font-mono-data text-[10px] uppercase tracking-widest px-3 py-1 rounded-full">
                    Most popular
                  </div>
                )}
                <p className="font-mono-data text-xs text-[#4a5568] uppercase tracking-widest mb-3">
                  {plan.name}
                </p>
                <div className="flex items-baseline gap-1 mb-2">
                  <span
                    className="font-serif text-4xl text-[#e8eaf0]"
                    style={{ fontFamily: "DM Serif Display, serif" }}
                  >
                    {plan.price === "Custom"
                      ? "Custom"
                      : billingAnnual && plan.price !== "Custom"
                      ? `$${Math.round(parseInt(plan.price.slice(1)) * 0.8).toLocaleString()}`
                      : plan.price}
                  </span>
                  {plan.period && <span className="text-sm text-[#4a5568]">{plan.period}</span>}
                </div>
                <p className="text-sm text-[#8895a7] mb-6">{plan.desc}</p>
                <button
                  className={`w-full py-2.5 rounded text-sm font-medium transition-colors mb-6 ${
                    plan.highlight
                      ? "bg-[#00d4a8] text-[#070b14] hover:bg-[#00bfa0]"
                      : "border border-white/10 text-[#e8eaf0] hover:border-white/20"
                  }`}
                >
                  {plan.cta}
                </button>
                <ul className="flex flex-col gap-3">
                  {plan.features.map((feat) => (
                    <li key={feat} className="flex items-start gap-2.5 text-sm text-[#8895a7]">
                      <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4 mt-0.5 flex-shrink-0">
                        <circle cx="8" cy="8" r="7" stroke="#00d4a8" strokeWidth="1" />
                        <path
                          d="M5 8l2 2 4-4"
                          stroke="#00d4a8"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      {feat}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 border-t border-white/[0.06]">
        <div className="max-w-7xl mx-auto">
          <div className="relative rounded-2xl overflow-hidden border border-[#00d4a8]/20 bg-gradient-to-br from-[#0d1f1a] to-[#070b14] p-12 md:p-20 text-center">
            <p className="font-mono-data text-xs text-[#00d4a8] uppercase tracking-widest mb-6">
              Get started today
            </p>
            <h2
              className="font-serif text-4xl md:text-6xl leading-tight mb-6 max-w-3xl mx-auto"
              style={{ fontFamily: "DM Serif Display, serif" }}
            >
              Your revenue stack,
              <br />
              <span className="italic">finally autonomous.</span>
            </h2>
            <p className="text-[#8895a7] text-lg mb-10 max-w-xl mx-auto">
              Join 1,200+ growth teams running AI agents on Axon. 14-day free trial, no credit card
              required.
            </p>
            <div className="flex flex-wrap gap-3 justify-center">
              <a
                href="#"
                className="inline-flex items-center gap-2 bg-[#00d4a8] text-[#070b14] font-semibold text-sm px-8 py-3.5 rounded hover:bg-[#00bfa0] transition-colors"
              >
                Start free trial
                <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4">
                  <path
                    d="M3 8h10M9 4l4 4-4 4"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </a>
              <a
                href="#"
                className="inline-flex items-center border border-white/10 text-sm text-[#e8eaf0] px-8 py-3.5 rounded hover:border-white/20 transition-colors"
              >
                Talk to sales
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-white/[0.06] py-16 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-[1fr_auto] gap-12 mb-12">
            <div className="max-w-xs">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-7 h-7 rounded bg-[#00d4a8] flex items-center justify-center">
                  <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
                    <path
                      d="M10 3l7 4v6l-7 4-7-4V7l7-4z"
                      stroke="#070b14"
                      strokeWidth="1.5"
                      strokeLinejoin="round"
                    />
                    <circle cx="10" cy="10" r="2" fill="#070b14" />
                  </svg>
                </div>
                <span className="font-semibold tracking-tight text-[#e8eaf0]">
                  Axon<span className="text-[#00d4a8]">AI</span>
                </span>
              </div>
              <p className="text-sm text-[#4a5568] leading-relaxed">
                Autonomous AI agents for growth and commerce teams. SOC 2 Type II certified.
              </p>
            </div>
            <div className="grid grid-cols-3 gap-12 text-sm">
              {[
                {
                  heading: "Platform",
                  links: ["Agents", "Revenue Intelligence", "Commerce", "Integrations", "Security"],
                },
                {
                  heading: "Company",
                  links: ["About", "Blog", "Careers", "Press", "Contact"],
                },
                {
                  heading: "Legal",
                  links: ["Privacy", "Terms", "DPA", "Security"],
                },
              ].map((col) => (
                <div key={col.heading}>
                  <p className="font-mono-data text-[10px] uppercase tracking-widest text-[#4a5568] mb-4">
                    {col.heading}
                  </p>
                  <ul className="flex flex-col gap-2.5">
                    {col.links.map((l) => (
                      <li key={l}>
                        <a href="#" className="text-[#8895a7] hover:text-[#e8eaf0] transition-colors">
                          {l}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
          <div className="border-t border-white/[0.06] pt-8 flex flex-wrap items-center justify-between gap-4">
            <p className="font-mono-data text-xs text-[#4a5568]">© 2026 AxonAI, Inc. All rights reserved.</p>
            <p className="font-mono-data text-xs text-[#2d3748]">SOC 2 · GDPR · CCPA · ISO 27001</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
