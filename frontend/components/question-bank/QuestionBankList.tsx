"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import {
  QuestionDifficultyBadge,
  QuestionStatusBadge
} from "@/components/question-bank/QuestionBadges";
import { QuestionReviewActions } from "@/components/question-bank/QuestionReviewActions";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/hooks/useAuth";
import {
  getClassLevels,
  getSubjects,
  getTopics
} from "@/lib/academics";
import { ApiError } from "@/lib/api";
import { getQuestions, getQuestionSources } from "@/lib/questionBank";
import type { ClassLevel, Subject, Topic } from "@/types/academics";
import type { CurrentUser } from "@/types/auth";
import type {
  Question,
  QuestionDifficulty,
  QuestionFilters,
  QuestionSource,
  QuestionSourceType,
  QuestionStatus
} from "@/types/questionBank";

type QuestionBankListProps = {
  mode: "admin" | "teacher";
  basePath: string;
};

const difficultyOptions: Array<{ value: QuestionDifficulty | ""; label: string }> = [
  { value: "", label: "All difficulties" },
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" }
];

const statusOptions: Array<{ value: QuestionStatus | ""; label: string }> = [
  { value: "", label: "All statuses" },
  { value: "draft", label: "Draft" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "archived", label: "Archived" }
];

const sourceTypeOptions: Array<{ value: QuestionSourceType | ""; label: string }> = [
  { value: "", label: "All source types" },
  { value: "jamb_past_question", label: "JAMB past question" },
  { value: "waec_past_question", label: "WAEC past question" },
  { value: "neco_past_question", label: "NECO past question" },
  { value: "teacher_created", label: "Teacher created" },
  { value: "ai_generated", label: "AI generated" },
  { value: "school_created", label: "School created" }
];

function truncate(value: string, limit = 150) {
  if (value.length <= limit) {
    return value;
  }
  return `${value.slice(0, limit)}...`;
}

function isPlatformAdmin(user: CurrentUser | null) {
  return Boolean(
    user && (user.role === "platform_admin" || user.is_superuser)
  );
}

function canEditQuestion(
  question: Question,
  mode: "admin" | "teacher",
  user: CurrentUser | null
) {
  if (isPlatformAdmin(user)) {
    return ["draft", "rejected"].includes(question.status);
  }

  if (mode === "admin") {
    return question.school !== null && ["draft", "rejected"].includes(question.status);
  }

  return question.status === "draft" && question.created_by === user?.id;
}

function canReviewQuestion(
  question: Question,
  mode: "admin" | "teacher",
  user: CurrentUser | null
) {
  if (mode !== "admin") {
    return false;
  }

  return isPlatformAdmin(user) || question.school !== null;
}

export function QuestionBankList({ mode, basePath }: QuestionBankListProps) {
  const { user } = useAuth();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [classLevels, setClassLevels] = useState<ClassLevel[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [sources, setSources] = useState<QuestionSource[]>([]);
  const [filters, setFilters] = useState<QuestionFilters>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isReferenceLoading, setIsReferenceLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const status = searchParams.get("status");
    if (status && statusOptions.some((option) => option.value === status)) {
      setFilters((current) => ({
        ...current,
        status: status as QuestionStatus
      }));
    }
  }, []);

  useEffect(() => {
    async function loadReferences() {
      try {
        const [subjectsData, classLevelsData, topicsData, sourcesData] =
          await Promise.all([
            getSubjects(),
            getClassLevels(),
            getTopics(),
            getQuestionSources()
          ]);
        setSubjects(subjectsData);
        setClassLevels(classLevelsData);
        setTopics(topicsData);
        setSources(sourcesData);
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load question bank filters."
        );
      } finally {
        setIsReferenceLoading(false);
      }
    }

    void loadReferences();
  }, []);

  const loadQuestions = useCallback(async () => {
    setIsLoading(true);
    try {
      setQuestions(await getQuestions(filters));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to load questions."
      );
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    void loadQuestions();
  }, [loadQuestions]);

  const filteredTopics = useMemo(() => {
    return topics.filter((topic) => {
      const matchesSubject = filters.subject
        ? topic.subject === Number(filters.subject)
        : true;
      const matchesClassLevel = filters.class_level
        ? topic.class_level === Number(filters.class_level)
        : true;
      return matchesSubject && matchesClassLevel;
    });
  }, [filters.class_level, filters.subject, topics]);

  function setFilter(name: keyof QuestionFilters, value: string) {
    setSuccess("");
    setFilters((current) => ({
      ...current,
      [name]: value,
      ...(name === "subject" || name === "class_level" ? { topic: "" } : {})
    }));
  }

  function updateQuestionInList(updatedQuestion: Question) {
    setQuestions((current) =>
      current.map((question) =>
        question.id === updatedQuestion.id ? updatedQuestion : question
      )
    );
  }

  const title = mode === "admin" ? "Question Bank" : "Teacher Question Bank";
  const description =
    mode === "admin"
      ? "Manage school-specific questions and review drafts for assignment use."
      : "Browse approved global questions and create draft school questions.";

  if (isLoading && !questions.length) {
    return <LoadingState label="Loading question bank..." />;
  }

  if (error && !questions.length && !isReferenceLoading) {
    return <EmptyState title="Question bank unavailable" description={error} />;
  }

  return (
    <>
      <PageHeader
        title={title}
        description={description}
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href={`${basePath}/ai-suggestions`}>
              <Button variant="secondary">AI Suggestions</Button>
            </Link>
            {mode === "admin" ? (
              <>
                <Link href="/admin/question-bank/quality">
                  <Button variant="secondary">Question Quality</Button>
                </Link>
                <Link href="/admin/question-bank/imports/new">
                  <Button variant="secondary">Import CSV</Button>
                </Link>
                <Link href="/admin/question-bank/imports">
                  <Button variant="secondary">Import History</Button>
                </Link>
              </>
            ) : null}
            <Link href={`${basePath}/new`}>
              <Button>Create Question</Button>
            </Link>
          </div>
        }
      />

      {mode === "admin" ? (
        <div className="mb-4 rounded-md border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-warning">
          Imported CSV questions are saved as drafts and must be approved before
          assignment generation can use them.
        </div>
      ) : null}

      {success ? (
        <div className="mb-4 rounded-md border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-success">
          {success}
        </div>
      ) : null}
      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <Card className="mb-4">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Input
            label="Search"
            value={String(filters.search ?? "")}
            placeholder="Question text"
            onChange={(event) => setFilter("search", event.target.value)}
          />
          <Select
            label="Subject"
            value={String(filters.subject ?? "")}
            options={[
              { value: "", label: "All subjects" },
              ...subjects.map((subject) => ({
                value: String(subject.id),
                label: subject.name
              }))
            ]}
            onChange={(event) => setFilter("subject", event.target.value)}
          />
          <Select
            label="Class level"
            value={String(filters.class_level ?? "")}
            options={[
              { value: "", label: "All class levels" },
              ...classLevels.map((classLevel) => ({
                value: String(classLevel.id),
                label: classLevel.name
              }))
            ]}
            onChange={(event) => setFilter("class_level", event.target.value)}
          />
          <Select
            label="Topic"
            value={String(filters.topic ?? "")}
            options={[
              { value: "", label: "All topics" },
              ...filteredTopics.map((topic) => ({
                value: String(topic.id),
                label: topic.title
              }))
            ]}
            onChange={(event) => setFilter("topic", event.target.value)}
          />
          <Select
            label="Difficulty"
            value={String(filters.difficulty ?? "")}
            options={difficultyOptions}
            onChange={(event) => setFilter("difficulty", event.target.value)}
          />
          <Select
            label="Status"
            value={String(filters.status ?? "")}
            options={statusOptions}
            onChange={(event) => setFilter("status", event.target.value)}
          />
          <Select
            label="Source"
            value={String(filters.source ?? "")}
            options={[
              { value: "", label: "All sources" },
              ...sources.map((source) => ({
                value: String(source.id),
                label: source.year ? `${source.name} (${source.year})` : source.name
              }))
            ]}
            onChange={(event) => setFilter("source", event.target.value)}
          />
          <Select
            label="Source type"
            value={String(filters.source_type ?? "")}
            options={sourceTypeOptions}
            onChange={(event) => setFilter("source_type", event.target.value)}
          />
        </div>
        <div className="mt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              setFilters({});
              setSuccess("");
            }}
          >
            Clear Filters
          </Button>
        </div>
      </Card>

      {isLoading ? (
        <LoadingState label="Loading questions..." />
      ) : (
        <DataTable<Question>
          data={questions}
          emptyTitle="No questions found"
          emptyDescription="Create a question or adjust the filters to find existing question bank items."
          columns={[
            {
              key: "question_text",
              header: "Question",
              render: (row) => (
                <div className="min-w-[18rem] max-w-xl">
                  <span className="block leading-6">
                    {truncate(row.question_text)}
                  </span>
                  <span className="mt-2 flex flex-wrap gap-2">
                    {row.has_diagram ? <Badge tone="brand">diagram</Badge> : null}
                    {row.needs_manual_review ? (
                      <Badge tone="warning">manual review</Badge>
                    ) : null}
                  </span>
                </div>
              )
            },
            {
              key: "subject_name",
              header: "Subject",
              render: (row) => row.subject_name ?? "Not set"
            },
            {
              key: "topic_title",
              header: "Topic",
              render: (row) => row.topic_title ?? "Not set"
            },
            {
              key: "class_level_name",
              header: "Class level",
              render: (row) => row.class_level_name ?? "Not set"
            },
            {
              key: "difficulty",
              header: "Difficulty",
              render: (row) => (
                <QuestionDifficultyBadge difficulty={row.difficulty} />
              )
            },
            {
              key: "status",
              header: "Status",
              render: (row) => <QuestionStatusBadge status={row.status} />
            },
            {
              key: "source_name",
              header: "Source",
              render: (row) => row.source_name ?? "No source"
            },
            {
              key: "created_by_name",
              header: "Created by",
              render: (row) => row.created_by_name ?? "System"
            },
            {
              key: "reviewed_by_name",
              header: "Reviewed by",
              render: (row) => row.reviewed_by_name ?? "Not reviewed"
            },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <div className="flex min-w-[14rem] flex-wrap gap-2">
                  <Link href={`${basePath}/${row.id}`}>
                    <Button variant="secondary">View</Button>
                  </Link>
                  {canEditQuestion(row, mode, user) ? (
                    <Link href={`${basePath}/${row.id}?mode=edit`}>
                      <Button variant="ghost">Edit</Button>
                    </Link>
                  ) : null}
                  <QuestionReviewActions
                    question={row}
                    canReview={canReviewQuestion(row, mode, user)}
                    onQuestionChange={updateQuestionInList}
                    onError={setError}
                    onSuccess={setSuccess}
                  />
                </div>
              )
            }
          ]}
        />
      )}
    </>
  );
}
