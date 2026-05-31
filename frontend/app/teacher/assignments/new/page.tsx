"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import {
  generateAssignmentFromTopic,
  getClassArms,
  getLessonLog,
  getTeacherAssignments,
  getTopics,
  publishAssignment
} from "@/lib/academics";
import { ApiError } from "@/lib/api";
import type {
  Assignment,
  ClassArm,
  LessonLog,
  TeacherAssignment,
  Topic
} from "@/types/academics";

function localDateTimeValue(value: string | null) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  const offsetMs = date.getTimezoneOffset() * 60 * 1000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

function uniqueById<T extends { id: number }>(items: T[]) {
  return Array.from(new Map(items.map((item) => [item.id, item])).values());
}

function notesPreview(notes: string) {
  if (!notes) {
    return "No notes added";
  }
  return notes.length > 120 ? `${notes.slice(0, 120)}...` : notes;
}

function AssignmentCreateForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const lessonLogId = searchParams.get("lessonLogId");
  const prefillClassArm = searchParams.get("classArm") ?? searchParams.get("class_arm");
  const prefillSubject = searchParams.get("subject");
  const prefillTopic = searchParams.get("topic");
  const prefillQuestionCount =
    searchParams.get("questionCount") ?? searchParams.get("question_count");
  const prefillTitle = searchParams.get("title");
  const prefillInstructions = searchParams.get("instructions");
  const isRemedial = searchParams.get("remedial") === "true";

  const [teacherAssignments, setTeacherAssignments] = useState<TeacherAssignment[]>([]);
  const [classArms, setClassArms] = useState<ClassArm[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [lessonLog, setLessonLog] = useState<LessonLog | null>(null);
  const [draftAssignment, setDraftAssignment] = useState<Assignment | null>(null);

  const [classArm, setClassArm] = useState("");
  const [subject, setSubject] = useState("");
  const [topic, setTopic] = useState("");
  const [title, setTitle] = useState("");
  const [instructions, setInstructions] = useState("");
  const [questionCount, setQuestionCount] = useState("10");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [dueAt, setDueAt] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingTopics, setIsLoadingTopics] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [assignmentRows, classArmRows] = await Promise.all([
          getTeacherAssignments({ is_active: true }),
          getClassArms()
        ]);
        setTeacherAssignments(assignmentRows);
        setClassArms(classArmRows);

        if (lessonLogId) {
          const lesson = await getLessonLog(lessonLogId);
          setLessonLog(lesson);
          setClassArm(String(lesson.class_arm));
          setSubject(String(lesson.subject));
          setTopic(String(lesson.topic));
          setTitle(`${lesson.topic_title ?? "Topic"} Practice`);
          setInstructions(
            lesson.notes ? `Based on lesson notes: ${notesPreview(lesson.notes)}` : ""
          );
        } else {
          if (prefillClassArm) {
            setClassArm(prefillClassArm);
          }
          if (prefillSubject) {
            setSubject(prefillSubject);
          }
          if (prefillTopic) {
            setTopic(prefillTopic);
          }
          if (prefillQuestionCount) {
            setQuestionCount(prefillQuestionCount);
          }
          if (prefillTitle) {
            setTitle(prefillTitle);
          }
          if (prefillInstructions) {
            setInstructions(prefillInstructions);
          }
        }
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load assignment form data."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadInitialData();
  }, [
    lessonLogId,
    prefillClassArm,
    prefillInstructions,
    prefillQuestionCount,
    prefillSubject,
    prefillTitle,
    prefillTopic
  ]);

  const selectedClassArm = useMemo(
    () => classArms.find((item) => String(item.id) === classArm),
    [classArm, classArms]
  );

  const classArmOptions = useMemo(() => {
    const items = uniqueById(
      teacherAssignments.map((assignment) => ({
        id: assignment.class_arm,
        label: assignment.class_arm_name ?? String(assignment.class_arm)
      }))
    );
    return items.map((item) => ({ value: String(item.id), label: item.label }));
  }, [teacherAssignments]);

  const selectedClassAssignments = useMemo(
    () =>
      teacherAssignments.filter(
        (assignment) => String(assignment.class_arm) === classArm
      ),
    [classArm, teacherAssignments]
  );

  const subjectOptions = useMemo(() => {
    const items = uniqueById(
      selectedClassAssignments.map((assignment) => ({
        id: assignment.subject,
        label: assignment.subject_name ?? String(assignment.subject)
      }))
    );
    return items.map((item) => ({ value: String(item.id), label: item.label }));
  }, [selectedClassAssignments]);

  const selectedAssignment = useMemo(
    () =>
      teacherAssignments.find(
        (assignment) =>
          String(assignment.class_arm) === classArm &&
          String(assignment.subject) === subject
      ),
    [classArm, subject, teacherAssignments]
  );

  useEffect(() => {
    if (lessonLog) {
      return;
    }

    if (classArm && subject && !selectedAssignment) {
      setSubject("");
      setTopic("");
    }
  }, [classArm, lessonLog, selectedAssignment, subject]);

  useEffect(() => {
    async function loadTopics() {
      if (!selectedAssignment && !lessonLog) {
        setTopics([]);
        return;
      }

      setIsLoadingTopics(true);
      setError("");
      try {
        const topicRows = await getTopics({
          subject: Number(subject),
          class_level: selectedClassArm?.class_level
        });
        const filtered = topicRows.filter(
          (item) =>
            item.subject === Number(subject) &&
            (!selectedClassArm || item.class_level === selectedClassArm.class_level)
        );
        setTopics(filtered);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Unable to load topics.");
      } finally {
        setIsLoadingTopics(false);
      }
    }

    if (subject) {
      void loadTopics();
    }
  }, [lessonLog, selectedAssignment, selectedClassArm, subject]);

  function validateForm() {
    if (!title.trim()) {
      return "Title is required.";
    }
    if (!classArm || !subject || !topic) {
      return "Class arm, subject, and topic are required.";
    }
    if (!selectedAssignment && !lessonLog) {
      return "Choose a class arm and subject assigned to you.";
    }
    if (!questionCount || Number(questionCount) < 1) {
      return "Question count must be a positive number.";
    }
    if (durationMinutes && Number(durationMinutes) < 1) {
      return "Duration must be positive if provided.";
    }
    if (startsAt && dueAt && new Date(startsAt) > new Date(dueAt)) {
      return "Due date cannot be before start date.";
    }
    return "";
  }

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsGenerating(true);
    try {
      const assignment = await generateAssignmentFromTopic({
        class_arm: Number(classArm),
        subject: Number(subject),
        topic: Number(topic),
        lesson_log: lessonLog ? lessonLog.id : null,
        title,
        instructions,
        question_count: Number(questionCount),
        duration_minutes: durationMinutes ? Number(durationMinutes) : null,
        starts_at: startsAt || null,
        due_at: dueAt || null
      });
      setDraftAssignment(assignment);
      setSuccess("Draft assignment generated.");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to generate assignment. Check that enough approved questions exist."
      );
    } finally {
      setIsGenerating(false);
    }
  }

  async function handlePublish() {
    if (!draftAssignment) {
      return;
    }

    setIsPublishing(true);
    setError("");
    setSuccess("");
    try {
      const published = await publishAssignment(draftAssignment.id);
      setSuccess("Assignment published.");
      router.push(`/teacher/assignments/${published.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to publish assignment.");
    } finally {
      setIsPublishing(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading assignment form..." />;
  }

  if (!teacherAssignments.length) {
    return (
      <>
        <PageHeader
          title="Create Assignment"
          description="Generate a draft assignment from approved topic questions."
        />
        <EmptyState
          title="No assigned classes yet"
          description="You need an active teacher assignment before generating assignments."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Create Assignment"
        description="Generate a draft assignment from approved questions, then publish when ready."
      />

      {lessonLog ? (
        <Card className="mb-6">
          <h2 className="text-base font-semibold text-ink">Lesson summary</h2>
          <p className="mt-2 text-sm font-medium text-muted">
            {lessonLog.class_arm_name} · {lessonLog.subject_name} ·{" "}
            {lessonLog.topic_title}
          </p>
          <p className="mt-2 text-sm text-muted">
            Taught at {new Intl.DateTimeFormat("en-NG", {
              dateStyle: "medium",
              timeStyle: "short"
            }).format(new Date(lessonLog.taught_at))}
          </p>
          <p className="mt-3 text-sm leading-6 text-muted">
            {notesPreview(lessonLog.notes)}
          </p>
        </Card>
      ) : null}

      {isRemedial ? (
        <Card className="mb-6 border-amber-100 bg-amber-50">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="warning" data-testid="assignment-remedial-badge">
              Remedial assignment
            </Badge>
            <span className="text-sm font-semibold text-warning">
              Prefilled from your remediation plan.
            </span>
          </div>
          <p className="mt-2 text-sm leading-6 text-muted">
            Review the fields, generate a draft from approved question-bank
            questions, then publish when ready.
          </p>
        </Card>
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

      <Card className="max-w-4xl">
        <form className="space-y-4" onSubmit={handleGenerate}>
          <Input
            label="Title"
            data-testid="assignment-title-input"
            value={title}
            required
            onChange={(event) => setTitle(event.target.value)}
          />

          <div className="grid gap-4 md:grid-cols-3">
            <Select
              label="Class arm"
              data-testid="assignment-class-arm-select"
              value={classArm}
              required
              disabled={Boolean(lessonLog)}
              options={[
                { value: "", label: "Select class arm" },
                ...classArmOptions
              ]}
              onChange={(event) => {
                setClassArm(event.target.value);
                setSubject("");
                setTopic("");
              }}
            />
            <Select
              label="Subject"
              data-testid="assignment-subject-select"
              value={subject}
              required
              disabled={Boolean(lessonLog)}
              options={[
                { value: "", label: "Select subject" },
                ...subjectOptions
              ]}
              onChange={(event) => {
                setSubject(event.target.value);
                setTopic("");
              }}
            />
            <Select
              label="Topic"
              data-testid="assignment-topic-select"
              value={topic}
              required
              disabled={Boolean(lessonLog)}
              options={[
                {
                  value: "",
                  label: isLoadingTopics ? "Loading topics..." : "Select topic"
                },
                ...topics.map((item) => ({
                  value: String(item.id),
                  label: item.title
                }))
              ]}
              onChange={(event) => setTopic(event.target.value)}
            />
          </div>

          {subject && !isLoadingTopics && !topics.length ? (
            <div className="rounded-md border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-warning">
              No topics were found for this subject and class level.
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-3">
            <Input
              label="Question count"
              data-testid="assignment-question-count-input"
              type="number"
              min={1}
              value={questionCount}
              required
              onChange={(event) => setQuestionCount(event.target.value)}
            />
            <Input
              label="Duration minutes"
              type="number"
              min={1}
              value={durationMinutes}
              onChange={(event) => setDurationMinutes(event.target.value)}
            />
            <Input
              label="Starts at"
              type="datetime-local"
              value={startsAt}
              onChange={(event) => setStartsAt(event.target.value)}
            />
          </div>

          <Input
            label="Due at"
            type="datetime-local"
            value={dueAt}
            onChange={(event) => setDueAt(event.target.value)}
          />

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-ink">
              Instructions
            </span>
            <textarea
              className="min-h-28 w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
              value={instructions}
              placeholder="Optional instructions for students"
              onChange={(event) => setInstructions(event.target.value)}
            />
          </label>

          <Button
            type="submit"
            isLoading={isGenerating}
            data-testid="assignment-generate-button"
          >
            Generate Draft Assignment
          </Button>
        </form>
      </Card>

      {draftAssignment ? (
        <Card className="mt-6" data-testid="assignment-draft-preview">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-ink">
                  Draft preview
                </h2>
                <Badge tone="warning" data-testid="assignment-status-badge">
                  {draftAssignment.status}
                </Badge>
              </div>
              <p className="mt-2 text-sm text-muted">
                {draftAssignment.assignment_questions.length} selected questions.
              </p>
            </div>
            <div className="flex gap-3">
              <Link href="/teacher/assignments">
                <Button variant="secondary">Save as Draft</Button>
              </Link>
              <Button
                isLoading={isPublishing}
                onClick={handlePublish}
                data-testid="assignment-publish-button"
              >
                Publish Assignment
              </Button>
            </div>
          </div>

          <div className="mt-5 space-y-3">
            {draftAssignment.assignment_questions.map((item) => (
              <div
                key={item.id}
                className="rounded-md border border-line bg-surface p-3"
              >
                <p className="text-sm font-semibold text-brand-700">
                  Question {item.order} · {item.marks} mark
                  {item.marks === 1 ? "" : "s"}
                </p>
                <p className="mt-2 text-sm leading-6 text-ink">
                  {item.question_detail?.question_text ?? `Question #${item.question}`}
                </p>
                <p className="mt-2 text-xs font-medium text-muted">
                  Options are not returned by the current assignment API.
                </p>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </>
  );
}

export default function NewTeacherAssignmentPage() {
  return (
    <Suspense fallback={<LoadingState label="Loading assignment form..." />}>
      <AssignmentCreateForm />
    </Suspense>
  );
}
