export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex min-h-40 items-center justify-center rounded-lg border border-line bg-white p-6 text-sm font-medium text-muted">
      {label}
    </div>
  );
}
