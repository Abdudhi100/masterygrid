"use client";

import { Button } from "@/components/ui/Button";

const csvTemplate = [
  [
    "subject",
    "class_level",
    "topic",
    "source_name",
    "source_type",
    "exam_body",
    "year",
    "difficulty",
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_option",
    "explanation"
  ].join(","),
  [
    "Mathematics",
    "SS2",
    "Quadratic Equations",
    "JAMB Mathematics",
    "jamb_past_question",
    "JAMB",
    "2024",
    "medium",
    "\"What is the sum of roots of x^2 - 5x + 6 = 0?\"",
    "2",
    "3",
    "5",
    "6",
    "C",
    "\"The sum of roots is -b/a = 5.\""
  ].join(",")
].join("\n");

export function CsvTemplateDownloadButton() {
  function handleDownload() {
    const blob = new Blob([csvTemplate], { type: "text/csv;charset=utf-8" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "masterygrid-question-import-template.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }

  return (
    <Button type="button" variant="secondary" onClick={handleDownload}>
      Download CSV Template
    </Button>
  );
}
