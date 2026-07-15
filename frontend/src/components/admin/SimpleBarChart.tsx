interface Props {
  data: [string, number][];
  color?: string;
}

export function SimpleBarChart({ data, color = "#7C5CFF" }: Props) {
  if (data.length === 0) {
    return <p className="py-6 text-center text-xs text-paper-500">No activity in this window yet.</p>;
  }
  const max = Math.max(...data.map(([, count]) => count), 1);

  return (
    <div className="flex h-32 items-end gap-1">
      {data.map(([day, count]) => (
        <div key={day} className="group relative flex-1">
          <div
            className="rounded-t-sm transition-opacity group-hover:opacity-80"
            style={{ height: `${Math.max(4, (count / max) * 100)}px`, backgroundColor: color }}
          />
          <div className="pointer-events-none absolute -top-8 left-1/2 hidden -translate-x-1/2 whitespace-nowrap rounded-md bg-ink-950 px-2 py-1 text-[10px] text-paper-100 group-hover:block">
            {day}: {count}
          </div>
        </div>
      ))}
    </div>
  );
}
