import { motion } from "framer-motion";
import { PenTool, Cpu, PlayCircle, Bug, Mic, FileCode2 } from "lucide-react";

const FEATURES = [
  {
    icon: PenTool,
    title: "Draw naturally, on anything",
    desc: "Full pressure-sensitive support for Huion, Wacom, and XP-Pen tablets, or just your mouse.",
  },
  {
    icon: Cpu,
    title: "AI flowchart recognition",
    desc: "Rough sketches are automatically cleaned into professional, aligned flowcharts.",
  },
  {
    icon: FileCode2,
    title: "Flowchart to code, and back",
    desc: "Generate Python, Java, C++, JavaScript and more — or paste code to get a flowchart.",
  },
  {
    icon: PlayCircle,
    title: "Execution simulator",
    desc: "Watch your flowchart run block by block, with live variable and memory state.",
  },
  {
    icon: Bug,
    title: "Bug detector",
    desc: "Catches missing arrows, disconnected nodes, and infinite loops before you run anything.",
  },
  {
    icon: Mic,
    title: "Voice mode",
    desc: "Say 'create a login flowchart' and watch the canvas build itself.",
  },
];

export function Features() {
  return (
    <section id="features" className="border-t border-white/[0.06] py-24">
      <div className="mx-auto max-w-6xl px-6">
        <div className="max-w-xl">
          <span className="label-eyebrow">What it does</span>
          <h2 className="mt-3 font-display text-3xl font-semibold text-paper-100">
            Everything between a sketch and shippable code.
          </h2>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, desc }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className="glass-panel rounded-2xl p-6"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/15">
                <Icon size={18} className="text-violet-400" />
              </div>
              <h3 className="font-display text-base font-medium text-paper-100">{title}</h3>
              <p className="mt-2 text-sm text-paper-500">{desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
