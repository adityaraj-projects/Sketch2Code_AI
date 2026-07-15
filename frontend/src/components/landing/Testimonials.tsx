const TESTIMONIALS = [
  {
    quote:
      "I sketched my OS scheduling algorithm on my tablet during a lecture and had working C code before class ended.",
    name: "Priya S.",
    role: "CS Undergrad",
  },
  {
    quote:
      "The execution simulator made recursion finally click for my students — they can see the call stack build up.",
    name: "Rohit M.",
    role: "Programming Instructor",
  },
  {
    quote:
      "Replaced three separate tools in my workflow — flowcharting, code generation, and complexity analysis in one place.",
    name: "Ananya K.",
    role: "SDE Intern",
  },
];

export function Testimonials() {
  return (
    <section id="testimonials" className="border-t border-white/[0.06] py-24">
      <div className="mx-auto max-w-6xl px-6">
        <span className="label-eyebrow">Who's using it</span>
        <h2 className="mt-3 font-display text-3xl font-semibold text-paper-100">
          Built for the way people actually learn to code.
        </h2>

        <div className="mt-12 grid grid-cols-1 gap-5 md:grid-cols-3">
          {TESTIMONIALS.map((t) => (
            <div key={t.name} className="glass-panel rounded-2xl p-6">
              <p className="text-sm leading-relaxed text-paper-300">"{t.quote}"</p>
              <div className="mt-5 flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-violet-500/20 font-display text-sm text-violet-300">
                  {t.name.charAt(0)}
                </div>
                <div>
                  <p className="text-sm font-medium text-paper-100">{t.name}</p>
                  <p className="text-xs text-paper-500">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
