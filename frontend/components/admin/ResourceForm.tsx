"use client";

import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";

export type FieldOption = {
  value: string;
  label: string;
};

export type ResourceField = {
  name: string;
  label: string;
  type:
    | "text"
    | "email"
    | "password"
    | "date"
    | "textarea"
    | "checkbox"
    | "select";
  required?: boolean;
  options?: FieldOption[];
  placeholder?: string;
  helper?: string;
};

export type FormState = Record<string, string | boolean>;

type ResourceFormProps = {
  fields: ResourceField[];
  values: FormState;
  onChange: (name: string, value: string | boolean) => void;
};

export function ResourceForm({ fields, values, onChange }: ResourceFormProps) {
  return (
    <>
      {fields.map((field) => {
        if (field.type === "checkbox") {
          return (
            <label
              key={field.name}
              className="flex items-start gap-3 rounded-md border border-line bg-surface p-3"
            >
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 rounded border-line text-brand-600 focus:ring-brand-100"
                checked={Boolean(values[field.name])}
                onChange={(event) => onChange(field.name, event.target.checked)}
              />
              <span>
                <span className="block text-sm font-semibold text-ink">
                  {field.label}
                </span>
                {field.helper ? (
                  <span className="mt-1 block text-sm text-muted">{field.helper}</span>
                ) : null}
              </span>
            </label>
          );
        }

        if (field.type === "select") {
          return (
            <Select
              key={field.name}
              label={field.label}
              value={String(values[field.name] ?? "")}
              required={field.required}
              options={[
                { value: "", label: field.placeholder ?? "Select an option" },
                ...(field.options ?? [])
              ]}
              onChange={(event) => onChange(field.name, event.target.value)}
            />
          );
        }

        if (field.type === "textarea") {
          return (
            <label key={field.name} className="block">
              <span className="mb-2 block text-sm font-medium text-ink">
                {field.label}
              </span>
              <textarea
                className="min-h-24 w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
                value={String(values[field.name] ?? "")}
                required={field.required}
                placeholder={field.placeholder}
                onChange={(event) => onChange(field.name, event.target.value)}
              />
            </label>
          );
        }

        return (
          <Input
            key={field.name}
            label={field.label}
            type={field.type}
            value={String(values[field.name] ?? "")}
            required={field.required}
            placeholder={field.placeholder}
            onChange={(event) => onChange(field.name, event.target.value)}
          />
        );
      })}
    </>
  );
}
