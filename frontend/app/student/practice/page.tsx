"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import { getClassLevels, getSubjects, getTopics } from "@/lib/academics";
import { ApiError } from "@/lib/api";
import { getPracticeSessions, startPracticeSession } from "@/lib/practice";
import type { ClassLevel, Subject, Topic } from "@/types/academics";
import type {
  PracticeDifficulty,
  PracticeSession,
  PracticeStartPayload,
  PracticeStatus
} from "@/types/practice";

const difficultyOptions: Array<{ value: PracticeDifficulty; label: string }> = [
  { value: "mixed", label: "Mixed" },
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" }
];

type FormState = {
  subject: string;
  topic: string;
  class_level: string;
  difficulty: PracticeDifficulty;
  question_count: string;
};

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

function humanize(value: string) {
  return value.replaceAll("_", " ");
}

function statusTone(status: PracticeStatus) {
  if (status === "submitted") {
    return "success";
  }
  if (status === "abandoned") {
    return "neutral";
  }
  return "warning";
}

function percentageLabel(value: string | number | null) {
  if (value === null || value === undefined || value === "") {
    return "Not scored";
  }

  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return "Not scored";
  }

  return `${numeric.toFixed(2)}%`;
}

export default function StudentPracticePage() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [classLevels, setClassLevels] = useState<ClassLevel[]>([]);
  const [sessions, setSessions] = useState<PracticeSession[]>([]);
  const [form, setForm] = useState<FormState>({
    subject: "",
    topic: "",
    class_level: "",
    difficulty: "mixed",
    question_count: "10"
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");

  const loadPageData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [subjectsData, topicsData, classLevelsData, sessionsData] =
        await Promise.all([
          getSubjects(),
          getTopics(),
          getClassLevels(),
          getPracticeSessions()
        ]);
      setSubjects(subjectsData);
      setTopics(topicsData);
      setClassLevels(classLevelsData);
      setSessions(sessionsData);
      setError("");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to load practice data."
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPageData();
  }, [loadPageData]);

  const filteredTopics = useMemo(() => {
    return topics.filter((topic) => {
      const matchesSubject = form.subject
        ? topic.subject === Number(form.subject)
        : true;
      const matchesClassLevel = form.class_level
        ? topic.class_level === Number(form.class_level)
        : true;
      return matchesSubject && matchesClassLevel;
    });
  }, [form.class_level, form.subject, topics]);

  function updateForm(name: keyof FormState, value: string) {
    setFormError("");
    setForm((current) => ({
      ...current,
      [name]: value,
      ...(name === "subject" || name === "class_level" ? { topic: "" } : {})
    }));
  }

  async function handleStartPractice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");

    const questionCount = Number(form.question_count);
    if (!form.subject) {
      setFormError("Select a subject to start practice.");
      return;
    }
    if (!Number.isInteger(questionCount) || questionCount <= 0) {
      setFormError("Question count must be a positive number.");
      return;
    }

    const payload: PracticeStartPayload = {
      subject: Number(form.subject),
      topic: form.topic ? Number(form.topic) : null,
      class_level: form.class_level ? Number(form.class_level) : null,
      difficulty: form.difficulty,
      question_count: questionCount
    };

    setIsStarting(true);
    try {
      const session = await startPracticeSession(payload);
      router.push(`/student/practice/${session.id}`);
    } catch (err) {
      setFormError(
        err instanceof ApiError
          ? err.message
          : "Unable to start practice. Check that approved questions exist."
      );
    } finally {
      setIsStarting(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading practice..." />;
  }

  if (error) {
    return <EmptyState title="Practice unavailable" description={error} />;
  }

  return (
    <>
      <PageHeader
        title="Practice"
        description="Start self-paced practice from approved question-bank questions."
      />

      <section className="grid gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <Card>
          <h2 className="text-base font-semibold text-ink">Start Practice</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Practice uses only approved active questions from the trusted question bank.
          </p>

          {formError ? (
            <div className="mt-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
              {formError}
            </div>
          ) : null}

          <form className="mt-5 space-y-4" onSubmit={handleStartPractice}>
            <Select
              label="Subject"
              value={form.subject}
              options={[
                { value: "", label: "Select subject" },
                ...subjects.map((subject) => ({
                  value: String(subject.id),
                  label: subject.name
                }))
              ]}
              onChange={(event) => updateForm("subject", event.target.value)}
            />
            <Select
              label="Class level"
              value={form.class_level}
              options={[
                { value: "", label: "Any class level" },
                ...classLevels.map((classLevel) => ({
                  value: String(classLevel.id),
                  label: classLevel.name
                }))
              ]}
              onChange={(event) => updateForm("class_level", event.target.value)}
            />
            <Select
              label="Topic"
              value={form.topic}
              options={[
                { value: "", label: "Any matching topic" },
                ...filteredTopics.map((topic) => ({
                  value: String(topic.id),
                  label: topic.title
                }))
              ]}
              onChange={(event) => updateForm("topic", event.target.value)}
            />
            <Select
              label="Difficulty"
              value={form.difficulty}
              options={difficultyOptions}
              onChange={(event) =>
                updateForm("difficulty", event.target.value as PracticeDifficulty)
              }
            />
            <Input
              label="Question count"
              type="number"
              min={1}
              max={100}
              value={form.question_count}
              onChange={(event) => updateForm("question_count", event.target.value)}
            />
            <Button type="submit" isLoading={isStarting}>
              Start Practice
            </Button>
          </form>
        </Card>

        <Card>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-ink">Practice History</h2>
              <p className="mt-2 text-sm leading-6 text-muted">
                Continue open sessions or review completed practice.
              </p>
            </div>
            <Button
              type="button"
              variant="secondary"
              onClick={() => void loadPageData()}
            >
              Refresh
            </Button>
          </div>

          <div className="mt-5 space-y-3">
            {sessions.length ? (
              sessions.map((session) => (
                <div
                  key={session.id}
                  className="rounded-md border border-line bg-surface p-4"
                >
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-semibold text-ink">
                          {session.subject_name}
                        </p>
                        <Badge tone={statusTone(session.status)}>
                          {humanize(session.status)}
                        </Badge>
                        <Badge tone="brand">{humanize(session.difficulty)}</Badge>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-muted">
                        {session.topic_title ?? "Any topic"} -{" "}
                        {session.class_level_name ?? "Any class level"} -{" "}
                        {session.question_count_requested} questions
                      </p>
                      <p className="mt-1 text-sm leading-6 text-muted">
                        Started {formatDate(session.started_at)} - Submitted{" "}
                        {formatDate(session.submitted_at)}
                      </p>
                      <p className="mt-1 text-sm font-semibold text-ink">
                        {session.status === "submitted"
                          ? `${session.score}/${session.total_marks} (${percentageLabel(
                              session.percentage
                            )})`
                          : "Not submitted"}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {session.status === "submitted" ? (
                        <Link href={`/student/practice/${session.id}/result`}>
                          <Button variant="secondary">View Result</Button>
                        </Link>
                      ) : (
                        <Link href={`/student/practice/${session.id}`}>
                          <Button>Continue</Button>
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <EmptyState
                title="No practice sessions yet"
                description="Start your first practice session using the form."
              />
            )}
          </div>
        </Card>
      </section>
    </>
  );
}
