"use client";

import { Input } from "@/components/ui/Input";
import type { QuestionOptionLabel } from "@/types/questionBank";

export const optionLabels: QuestionOptionLabel[] = ["A", "B", "C", "D"];

export type OptionTexts = Record<QuestionOptionLabel, string>;

type QuestionOptionsEditorProps = {
  optionTexts: OptionTexts;
  correctOption: QuestionOptionLabel;
  onOptionTextChange: (label: QuestionOptionLabel, value: string) => void;
  onCorrectOptionChange: (label: QuestionOptionLabel) => void;
};

export function QuestionOptionsEditor({
  optionTexts,
  correctOption,
  onOptionTextChange,
  onCorrectOptionChange
}: QuestionOptionsEditorProps) {
  return (
    <div>
      <p className="mb-3 text-sm font-medium text-ink">Options</p>
      <div className="grid gap-3 md:grid-cols-2">
        {optionLabels.map((label) => (
          <div key={label} className="rounded-md border border-line bg-surface p-3">
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-ink">Option {label}</p>
              <label className="flex items-center gap-2 text-sm font-medium text-muted">
                <input
                  type="radio"
                  name="correct-option"
                  className="h-4 w-4 border-line text-brand-600 focus:ring-brand-100"
                  checked={correctOption === label}
                  onChange={() => onCorrectOptionChange(label)}
                />
                Correct
              </label>
            </div>
            <Input
              label={`Option ${label} text`}
              value={optionTexts[label]}
              required
              onChange={(event) => onOptionTextChange(label, event.target.value)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
