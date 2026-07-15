import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

const CODE_LINES = [
  "def check_eligibility(age, income):",
  "    if age >= 18:",
  "        if income > 25000:",
  "            return \"Approved\"",
  "        return \"Review needed\"",
  "    return \"Rejected\"",
];

export function Hero() {
  return (
    <section className="relative overflow-hidden pb-24 pt-40">
      <div className="absolute inset-0 bg-sketch-glow" />
      <div className="absolute inset-0 bg-grid-pattern bg-[length:36px_36px] opacity-30" />

      <div className="relative mx-auto max-w-6xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mx-auto max-w-2xl text-center"
        >
          <span className="label-eyebrow">AI-Powered Visual Programming</span>
          <h1 className="mt-4 font-display text-4xl font-semibold leading-tight text-paper-100 sm:text-5xl">
            Draw Logic. Generate Code.
            <br /> Understand Algorithms.
          </h1>
          <p className="mt-5 text-base text-paper-300">
            Sketch a flowchart by hand or on a tablet — Sketch2Code AI cleans it up, explains the
            logic, and turns it into working code in the language of your choice.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link to="/signup" className="btn-primary">
              Start drawing free <ArrowRight size={16} />
            </Link>
            <a href="#features" className="btn-secondary">
              See how it works
            </a>
          </div>
        </motion.div>

        {/* Signature element: rough sketch on the left resolves into clean code on the right */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="glass-panel relative mx-auto mt-16 grid max-w-4xl grid-cols-1 overflow-hidden rounded-2xl md:grid-cols-2"
        >
          <div className="border-b border-white/[0.06] p-6 md:border-b-0 md:border-r">
            <span className="label-eyebrow">01 — Sketch</span>
            <svg viewBox="0 0 260 220" className="mt-4 w-full">
              <rect x="90" y="8" width="80" height="34" rx="8" fill="none" stroke="#7C5CFF" strokeWidth="2" />
              <text x="130" y="29" textAnchor="middle" fontSize="11" fill="#EDEBE6" fontFamily="Inter">Start</text>

              <path d="M130 42 L130 62" stroke="#7C5CFF" strokeWidth="2" fill="none" strokeDasharray="5 4" className="animate-dash-flow" />

              <path d="M130 66 L180 96 L130 126 L80 96 Z" fill="none" stroke="#7C5CFF" strokeWidth="2" />
              <text x="130" y="100" textAnchor="middle" fontSize="10" fill="#EDEBE6" fontFamily="Inter">age &gt;= 18?</text>

              <path d="M130 126 L130 146" stroke="#7C5CFF" strokeWidth="2" fill="none" strokeDasharray="5 4" className="animate-dash-flow" />

              <rect x="70" y="150" width="120" height="34" rx="8" fill="none" stroke="#2EE6A6" strokeWidth="2" />
              <text x="130" y="171" textAnchor="middle" fontSize="10" fill="#EDEBE6" fontFamily="Inter">Check income</text>
            </svg>
          </div>

          <div className="bg-ink-950/60 p-6 font-mono text-[13px] leading-relaxed">
            <span className="label-eyebrow">02 — Generated code</span>
            <pre className="mt-4 overflow-x-auto text-paper-300">
              {CODE_LINES.map((line, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 + i * 0.12 }}
                >
                  <span className="mr-3 select-none text-paper-500">{i + 1}</span>
                  {line}
                </motion.div>
              ))}
            </pre>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
