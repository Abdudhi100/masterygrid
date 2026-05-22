"use client";

import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";

type FormModalProps = {
  title: string;
  isOpen: boolean;
  isSubmitting?: boolean;
  submitLabel?: string;
  onClose: () => void;
  onSubmit: () => void;
  children: ReactNode;
};

export function FormModal({
  title,
  isOpen,
  isSubmitting = false,
  submitLabel = "Save",
  onClose,
  onSubmit,
  children
}: FormModalProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/35 px-4 py-6">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white shadow-soft">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-lg font-semibold text-ink">{title}</h2>
          <button
            className="rounded-md px-2 py-1 text-sm font-semibold text-muted hover:bg-surface hover:text-ink"
            type="button"
            onClick={onClose}
          >
            Close
          </button>
        </div>
        <form
          className="space-y-4 p-5"
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit();
          }}
        >
          {children}
          <div className="flex justify-end gap-3 border-t border-line pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isSubmitting}>
              {submitLabel}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
