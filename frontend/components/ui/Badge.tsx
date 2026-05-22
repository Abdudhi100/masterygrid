type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

const toneClasses: Record<BadgeTone, string> = {
  neutral: "bg-slate-100 text-slate-700",
  success: "bg-emerald-50 text-success",
  warning: "bg-amber-50 text-warning",
  danger: "bg-red-50 text-danger",
  brand: "bg-brand-50 text-brand-700"
};

export function Badge({
  children,
  tone = "neutral"
}: {
  children: string;
  tone?: BadgeTone;
}) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${toneClasses[tone]}`}
    >
      {children}
    </span>
  );
}
