import { Check } from "lucide-react";
import { Link } from "react-router-dom";
import clsx from "clsx";

const PLANS = [
  {
    name: "Student",
    price: "Free",
    tagline: "For learning and coursework",
    features: ["3 active projects", "5 code exports / language", "Execution simulator", "Community templates"],
    highlighted: false,
  },
  {
    name: "Pro",
    price: "₹499/mo",
    tagline: "For serious builders",
    features: ["Unlimited projects", "All 10 languages", "AI bug detector", "Voice mode", "Priority AI credits"],
    highlighted: true,
  },
  {
    name: "Team",
    price: "₹1,499/mo",
    tagline: "For classrooms & small teams",
    features: ["Everything in Pro", "Realtime collaboration", "Shared template library", "Admin analytics"],
    highlighted: false,
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="border-t border-white/[0.06] py-24">
      <div className="mx-auto max-w-6xl px-6">
        <div className="max-w-xl">
          <span className="label-eyebrow">Pricing</span>
          <h2 className="mt-3 font-display text-3xl font-semibold text-paper-100">
            Simple pricing, upgrade when you outgrow free.
          </h2>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-5 md:grid-cols-3">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={clsx(
                "relative rounded-2xl border p-7",
                plan.highlighted
                  ? "border-violet-500/50 bg-violet-500/[0.06] shadow-glow-violet"
                  : "border-white/[0.06] bg-ink-900/60"
              )}
            >
              {plan.highlighted && (
                <span className="absolute -top-3 left-7 rounded-full bg-violet-500 px-3 py-1 text-[11px] font-medium text-white">
                  Most popular
                </span>
              )}
              <h3 className="font-display text-lg font-medium text-paper-100">{plan.name}</h3>
              <p className="mt-1 text-sm text-paper-500">{plan.tagline}</p>
              <p className="mt-5 font-display text-3xl font-semibold text-paper-100">{plan.price}</p>

              <ul className="mt-6 space-y-2.5">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-paper-300">
                    <Check size={15} className="text-mint-400" /> {f}
                  </li>
                ))}
              </ul>

              <Link
                to="/signup"
                className={clsx("mt-7 block w-full rounded-xl py-2.5 text-center text-sm font-medium", plan.highlighted ? "bg-violet-500 text-white hover:bg-violet-600" : "border border-white/10 text-paper-100 hover:bg-white/[0.05]")}
              >
                Get started
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
