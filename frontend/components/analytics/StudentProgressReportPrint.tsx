"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ApiError } from "@/lib/api";
import { getStudentProgressReport } from "@/lib/analytics";
import type {
  StudentProgressAssignmentResult,
  StudentProgressMissedAssignment,
  StudentProgressPracticeSession,
  StudentProgressRecommendation,
  StudentProgressReport as StudentProgressReportType,
  StudentProgressSubjectBreakdown,
  StudentProgressTopic,
  StudentProgressTopicBreakdown
} from "@/types/analytics";

function formatDate(value?: string | null) {
  if (!value) {
    return "Not set";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not set";
  }

  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function formatPercentage(value?: number | null) {
  if (value === null || value === undefined) {
    return "0.00%";
  }
  return `${Number(value).toFixed(2)}%`;
}

function titleCase(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function PrintSection({
  title,
  children
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="print-card">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function KeyValueGrid({
  items,
  testId
}: {
  items: Array<{ label: string; value: string | number }>;
  testId?: string;
}) {
  return (
    <dl className="print-key-grid" data-testid={testId}>
      {items.map((item) => (
        <div key={item.label}>
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

function PrintTable<T>({
  columns,
  rows,
  emptyText
}: {
  columns: Array<{ header: string; render: (row: T) => React.ReactNode }>;
  rows: T[];
  emptyText: string;
}) {
  if (!rows.length) {
    return <p className="print-empty">{emptyText}</p>;
  }

  return (
    <div className="print-table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.header}>{column.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column.header}>{column.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RecommendationList({
  rows
}: {
  rows: StudentProgressRecommendation[];
}) {
  if (!rows.length) {
    return <p className="print-empty">No recommendations yet.</p>;
  }

  return (
    <ol className="print-list">
      {rows.map((row, index) => (
        <li key={`${row.topic_id ?? "general"}-${index}`}>
          <strong>{row.recommended_action}</strong>
          <span>{row.reason}</span>
          {row.topic_title ? (
            <span>
              {row.subject_name} - {row.topic_title}
            </span>
          ) : null}
        </li>
      ))}
    </ol>
  );
}

export function StudentProgressReportPrint({
  studentId,
  backHref
}: {
  studentId: string;
  backHref: string;
}) {
  const [report, setReport] = useState<StudentProgressReportType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadReport = useCallback(async () => {
    try {
      setReport(await getStudentProgressReport(studentId));
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to load printable progress report."
      );
    } finally {
      setIsLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    document.body.classList.add("masterygrid-print-view");
    return () => {
      document.body.classList.remove("masterygrid-print-view");
    };
  }, []);

  useEffect(() => {
    void loadReport();
  }, [loadReport]);

  function handlePrint() {
    window.print();
  }

  if (isLoading) {
    return <LoadingState label="Loading printable progress report..." />;
  }

  if (error) {
    return <EmptyState title="Print view unavailable" description={error} />;
  }

  if (!report) {
    return (
      <EmptyState
        title="No printable report"
        description="This student progress report could not be loaded."
      />
    );
  }

  return (
    <div className="print-page-shell" data-testid="student-progress-print-page">
      <div className="print-controls">
        <Link
          href={backHref}
          className="print-back-link"
          data-testid="student-progress-print-back-link"
        >
          Back to Report
        </Link>
        <Button
          onClick={handlePrint}
          data-testid="student-progress-print-button"
        >
          Print / Save as PDF
        </Button>
      </div>

      <article className="print-document">
        <header className="print-header">
          <div>
            <p className="print-brand">MasteryGrid</p>
            <h1>Student Progress Report</h1>
            <p>{report.student.school ?? "School not set"}</p>
          </div>
          <div className="print-generated">
            <span>Generated</span>
            <strong>{formatDate(report.generated_at)}</strong>
          </div>
        </header>

        <PrintSection title="Student Identity">
          <KeyValueGrid
            items={[
              { label: "Name", value: report.student.full_name },
              { label: "Email", value: report.student.email },
              {
                label: "Admission number",
                value: report.student.admission_number ?? "Not set"
              },
              { label: "Class arm", value: report.student.class_arm ?? "Not set" }
            ]}
          />
        </PrintSection>

        <PrintSection title="Summary">
          <KeyValueGrid
            testId="student-progress-print-summary"
            items={[
              {
                label: "Assignment average",
                value: formatPercentage(report.summary.assignment_average)
              },
              {
                label: "Practice average",
                value: formatPercentage(report.summary.practice_average)
              },
              {
                label: "Overall average",
                value: formatPercentage(report.summary.overall_average)
              },
              { label: "Risk level", value: titleCase(report.summary.risk_level) },
              {
                label: "Graded assignments",
                value: report.summary.graded_assignments_count
              },
              {
                label: "Missed assignments",
                value: report.summary.missed_assignments_count
              },
              {
                label: "Practice sessions",
                value: report.summary.practice_sessions_count
              },
              { label: "Weak topics", value: report.summary.weak_topic_count }
            ]}
          />
        </PrintSection>

        <PrintSection title="Assignment Performance">
          <PrintTable<StudentProgressAssignmentResult>
            rows={report.assignment_performance.recent_results}
            emptyText="No graded assignment results yet."
            columns={[
              { header: "Assignment", render: (row) => row.assignment_title },
              { header: "Subject", render: (row) => row.subject_name },
              { header: "Topic", render: (row) => row.topic_title },
              {
                header: "Score",
                render: (row) => `${row.score}/${row.total_marks}`
              },
              {
                header: "Percentage",
                render: (row) => formatPercentage(row.percentage)
              },
              { header: "Graded", render: (row) => formatDate(row.graded_at) }
            ]}
          />
        </PrintSection>

        <PrintSection title="Practice Performance">
          <PrintTable<StudentProgressPracticeSession>
            rows={report.practice_performance.recent_sessions}
            emptyText="No submitted practice sessions yet."
            columns={[
              { header: "Subject", render: (row) => row.subject_name },
              { header: "Topic", render: (row) => row.topic_title ?? "Mixed topic" },
              { header: "Difficulty", render: (row) => titleCase(row.difficulty) },
              {
                header: "Score",
                render: (row) => `${row.score}/${row.total_marks}`
              },
              {
                header: "Percentage",
                render: (row) => formatPercentage(row.percentage)
              },
              { header: "Submitted", render: (row) => formatDate(row.submitted_at) }
            ]}
          />
        </PrintSection>

        <div className="print-two-column">
          <PrintSection title="Assignment Subjects">
            <PrintTable<StudentProgressSubjectBreakdown>
              rows={report.assignment_performance.subject_breakdown}
              emptyText="No assignment subject breakdown yet."
              columns={[
                { header: "Subject", render: (row) => row.subject_name },
                {
                  header: "Average",
                  render: (row) => formatPercentage(row.average_percentage)
                },
                {
                  header: "Graded",
                  render: (row) => row.graded_assignments_count ?? 0
                }
              ]}
            />
          </PrintSection>

          <PrintSection title="Practice Topics">
            <PrintTable<StudentProgressTopicBreakdown>
              rows={report.practice_performance.topic_breakdown}
              emptyText="No practice topic breakdown yet."
              columns={[
                { header: "Topic", render: (row) => row.topic_title },
                {
                  header: "Average",
                  render: (row) => formatPercentage(row.average_percentage)
                },
                {
                  header: "Answered",
                  render: (row) => row.questions_answered ?? 0
                }
              ]}
            />
          </PrintSection>
        </div>

        <div className="print-two-column">
          <PrintSection title="Weak Topics">
            <PrintTable<StudentProgressTopic>
              rows={report.weak_topics}
              emptyText="No weak topics detected yet."
              columns={[
                { header: "Subject", render: (row) => row.subject_name },
                { header: "Topic", render: (row) => row.topic_title },
                {
                  header: "Average",
                  render: (row) => formatPercentage(row.average_percentage)
                }
              ]}
            />
          </PrintSection>

          <PrintSection title="Strong Topics">
            <PrintTable<StudentProgressTopic>
              rows={report.strong_topics}
              emptyText="No strong topics detected yet."
              columns={[
                { header: "Subject", render: (row) => row.subject_name },
                { header: "Topic", render: (row) => row.topic_title },
                {
                  header: "Average",
                  render: (row) => formatPercentage(row.average_percentage)
                }
              ]}
            />
          </PrintSection>
        </div>

        <PrintSection title="Missed Assignments">
          <PrintTable<StudentProgressMissedAssignment>
            rows={report.assignment_performance.missed_assignments}
            emptyText="No missed assignments recorded."
            columns={[
              { header: "Assignment", render: (row) => row.title },
              { header: "Subject", render: (row) => row.subject },
              { header: "Topic", render: (row) => row.topic },
              { header: "Due", render: (row) => formatDate(row.due_at) }
            ]}
          />
        </PrintSection>

        <PrintSection title="Recommendations / Next Steps">
          <div data-testid="student-progress-print-recommendations">
            <RecommendationList rows={report.recommendations} />
          </div>
        </PrintSection>

        <footer className="print-footer">Generated by MasteryGrid</footer>
      </article>

      <style jsx global>{`
        body.masterygrid-print-view {
          background: #f8fafc;
        }

        body.masterygrid-print-view aside,
        body.masterygrid-print-view header.sticky,
        body.masterygrid-print-view div.border-b.border-line.bg-white.px-4.py-3.lg\\:hidden {
          display: none !important;
        }

        body.masterygrid-print-view main {
          max-width: none !important;
          padding: 0 !important;
        }

        .print-page-shell {
          min-height: 100vh;
          background: #f8fafc;
          color: #111827;
          padding: 24px;
        }

        .print-controls {
          margin: 0 auto 16px;
          display: flex;
          max-width: 960px;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .print-back-link {
          color: #334155;
          font-size: 14px;
          font-weight: 700;
          text-decoration: underline;
        }

        .print-document {
          margin: 0 auto;
          max-width: 960px;
          background: #ffffff;
          box-shadow: 0 12px 35px rgba(15, 23, 42, 0.12);
          padding: 40px;
        }

        .print-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 24px;
          border-bottom: 2px solid #111827;
          padding-bottom: 18px;
        }

        .print-brand {
          margin: 0 0 8px;
          color: #1d4ed8;
          font-size: 14px;
          font-weight: 800;
          letter-spacing: 0;
        }

        .print-header h1 {
          margin: 0;
          color: #111827;
          font-size: 28px;
          line-height: 1.2;
        }

        .print-header p {
          margin: 8px 0 0;
          color: #475569;
          font-size: 14px;
        }

        .print-generated {
          min-width: 180px;
          text-align: right;
          color: #475569;
          font-size: 12px;
        }

        .print-generated span,
        .print-generated strong {
          display: block;
        }

        .print-generated strong {
          margin-top: 4px;
          color: #111827;
          font-size: 13px;
        }

        .print-card {
          break-inside: avoid;
          margin-top: 24px;
          border: 1px solid #d1d5db;
          padding: 18px;
        }

        .print-card h2 {
          margin: 0 0 14px;
          color: #111827;
          font-size: 16px;
        }

        .print-key-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 12px;
        }

        .print-key-grid dt {
          color: #64748b;
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
        }

        .print-key-grid dd {
          margin: 4px 0 0;
          color: #111827;
          font-size: 14px;
          font-weight: 700;
          overflow-wrap: anywhere;
        }

        .print-table-wrap {
          overflow-x: auto;
        }

        .print-table-wrap table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }

        .print-table-wrap th,
        .print-table-wrap td {
          border: 1px solid #d1d5db;
          padding: 8px;
          text-align: left;
          vertical-align: top;
        }

        .print-table-wrap th {
          background: #f1f5f9;
          color: #334155;
          font-weight: 800;
        }

        .print-empty {
          margin: 0;
          color: #64748b;
          font-size: 13px;
        }

        .print-two-column {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
          gap: 18px;
        }

        .print-list {
          margin: 0;
          padding-left: 20px;
        }

        .print-list li {
          margin-bottom: 12px;
          break-inside: avoid;
        }

        .print-list strong,
        .print-list span {
          display: block;
        }

        .print-list strong {
          color: #111827;
          font-size: 13px;
        }

        .print-list span {
          margin-top: 3px;
          color: #475569;
          font-size: 12px;
          line-height: 1.5;
        }

        .print-footer {
          margin-top: 28px;
          border-top: 1px solid #d1d5db;
          padding-top: 12px;
          color: #64748b;
          font-size: 12px;
          text-align: center;
        }

        @media (max-width: 760px) {
          .print-page-shell {
            padding: 12px;
          }

          .print-controls,
          .print-header {
            flex-direction: column;
          }

          .print-generated {
            text-align: left;
          }

          .print-document {
            padding: 20px;
          }

          .print-key-grid,
          .print-two-column {
            grid-template-columns: 1fr;
          }
        }

        @media print {
          @page {
            size: A4;
            margin: 14mm;
          }

          html,
          body {
            background: #ffffff !important;
          }

          body.masterygrid-print-view aside,
          body.masterygrid-print-view header,
          body.masterygrid-print-view nav,
          body.masterygrid-print-view .print-controls {
            display: none !important;
          }

          body.masterygrid-print-view main {
            padding: 0 !important;
          }

          .print-page-shell {
            min-height: auto;
            background: #ffffff !important;
            padding: 0 !important;
          }

          .print-document {
            max-width: none;
            box-shadow: none !important;
            padding: 0;
          }

          .print-card {
            break-inside: avoid;
            page-break-inside: avoid;
          }

          .print-table-wrap {
            overflow: visible;
          }

          .print-table-wrap tr {
            break-inside: avoid;
            page-break-inside: avoid;
          }
        }
      `}</style>
    </div>
  );
}
