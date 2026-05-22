"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import { ApiError } from "@/lib/api";
import {
  createLessonLog,
  getAcademicSessions,
  getClassArms,
  getTeacherAssignments,
  getTerms,
  getTopics
} from "@/lib/academics";
import type {
  AcademicSession,
  ClassArm,
  LessonLog,
  TeacherAssignment,
  Term,
  Topic
} from "@/types/academics";

function localDateTimeValue(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

function uniqueById<T extends { id: number }>(items: T[]) {
  return Array.from(new Map(items.map((item) => [item.id, item])).values());
}

export default function NewLessonPage() {
  const [assignments, setAssignments] = useState<TeacherAssignment[]>([]);
  const [classArms, setClassArms] = useState<ClassArm[]>([]);
  const [sessions, setSessions] = useState<AcademicSession[]>([]);
  const [terms, setTerms] = useState<Term[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [classArm, setClassArm] = useState("");
  const [subject, setSubject] = useState("");
  const [topic, setTopic] = useState("");
  const [academicSession, setAcademicSession] = useState("");
  const [term, setTerm] = useState("");
  const [taughtAt, setTaughtAt] = useState(localDateTimeValue());
  const [notes, setNotes] = useState("");
  const [createdLesson, setCreatedLesson] = useState<LessonLog | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingTopics, setIsLoadingTopics] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [assignmentRows, classArmRows, sessionRows, termRows] = await Promise.all([
          getTeacherAssignments({ is_active: true }),
          getClassArms(),
          getAcademicSessions(),
          getTerms()
        ]);
        setAssignments(assignmentRows);
        setClassArms(classArmRows);
        setSessions(sessionRows);
        setTerms(termRows);
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load lesson form data."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadInitialData();
  }, []);

  const classArmOptions = useMemo(() => {
    const items = uniqueById(
      assignments.map((assignment) => ({
        id: assignment.class_arm,
        label: assignment.class_arm_name ?? String(assignment.class_arm)
      }))
    );
    return items.map((item) => ({ value: String(item.id), label: item.label }));
  }, [assignments]);

  const selectedClassAssignments = useMemo(
    () =>
      assignments.filter(
        (assignment) => String(assignment.class_arm) === classArm
      ),
    [assignments, classArm]
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
      assignments.find(
        (assignment) =>
          String(assignment.class_arm) === classArm &&
          String(assignment.subject) === subject
      ),
    [assignments, classArm, subject]
  );

  const selectedClassArm = useMemo(
    () => classArms.find((item) => String(item.id) === classArm),
    [classArm, classArms]
  );

  useEffect(() => {
    if (!classArm) {
      setSubject("");
      setTopic("");
      setTopics([]);
      return;
    }

    if (subject && !subjectOptions.some((option) => option.value === subject)) {
      setSubject("");
      setTopic("");
      setTopics([]);
    }
  }, [classArm, subject, subjectOptions]);

  useEffect(() => {
    async function loadTopics() {
      if (!selectedAssignment) {
        setTopics([]);
        setTopic("");
        return;
      }

      setIsLoadingTopics(true);
      setError("");
      try {
        const topicRows = await getTopics({
          subject: selectedAssignment.subject,
          class_level: selectedClassArm?.class_level
        });
        const filtered = topicRows.filter(
          (item) =>
            item.subject === selectedAssignment.subject &&
            (!selectedClassArm || item.class_level === selectedClassArm.class_level)
        );
        setTopics(filtered);
        if (topic && !filtered.some((item) => String(item.id) === topic)) {
          setTopic("");
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Unable to load topics.");
      } finally {
        setIsLoadingTopics(false);
      }
    }

    void loadTopics();
  }, [selectedAssignment, selectedClassArm, topic]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!selectedAssignment) {
      setError("Choose a class arm and subject assigned to you.");
      return;
    }

    if (!topic) {
      setError("Choose a topic for this lesson.");
      return;
    }

    setIsSubmitting(true);
    try {
      const lesson = await createLessonLog({
        class_arm: Number(classArm),
        subject: Number(subject),
        topic: Number(topic),
        academic_session: academicSession ? Number(academicSession) : null,
        term: term ? Number(term) : null,
        taught_at: taughtAt,
        notes
      });
      setCreatedLesson(lesson);
      setSuccess("Lesson logged successfully.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to log lesson.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading lesson form..." />;
  }

  if (!assignments.length) {
    return (
      <>
        <PageHeader
          title="Log Lesson"
          description="Log a taught topic after your school admin assigns you to classes and subjects."
        />
        <EmptyState
          title="No assigned classes yet"
          description="You need an active teacher assignment before you can log lessons."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Log Lesson"
        description="Record the class, subject, topic, and date taught."
      />

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

      {createdLesson ? (
        <Card className="mb-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-ink">Lesson saved</h2>
              <p className="mt-1 text-sm text-muted">
                You can now generate an assignment from this lesson.
              </p>
            </div>
            <div className="flex gap-3">
              <Link href="/teacher/lessons">
                <Button variant="secondary">View Lessons</Button>
              </Link>
              <Link href={`/teacher/assignments/new?lessonLogId=${createdLesson.id}`}>
                <Button>Generate Assignment from this Lesson</Button>
              </Link>
            </div>
          </div>
        </Card>
      ) : null}

      <Card className="max-w-3xl">
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="grid gap-4 md:grid-cols-2">
            <Select
              label="Class arm"
              value={classArm}
              required
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
              value={subject}
              required
              options={[
                { value: "", label: "Select subject" },
                ...subjectOptions
              ]}
              onChange={(event) => {
                setSubject(event.target.value);
                setTopic("");
              }}
            />
          </div>

          <Select
            label="Topic"
            value={topic}
            required
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

          {selectedAssignment && !isLoadingTopics && !topics.length ? (
            <div className="rounded-md border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-warning">
              No topics exist yet for this assigned subject. Ask a school admin to add
              topics for the matching class level.
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-3">
            <Select
              label="Academic session"
              value={academicSession}
              options={[
                { value: "", label: "Optional" },
                ...sessions.map((session) => ({
                  value: String(session.id),
                  label: session.name
                }))
              ]}
              onChange={(event) => setAcademicSession(event.target.value)}
            />
            <Select
              label="Term"
              value={term}
              options={[
                { value: "", label: "Optional" },
                ...terms.map((item) => ({
                  value: String(item.id),
                  label: `${item.academic_session_name ?? "Session"} - ${
                    item.term_name ?? item.name
                  }`
                }))
              ]}
              onChange={(event) => setTerm(event.target.value)}
            />
            <Input
              label="Taught at"
              type="datetime-local"
              value={taughtAt}
              required
              onChange={(event) => setTaughtAt(event.target.value)}
            />
          </div>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-ink">Notes</span>
            <textarea
              className="min-h-28 w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
              value={notes}
              placeholder="Optional lesson notes"
              onChange={(event) => setNotes(event.target.value)}
            />
          </label>

          <Button type="submit" isLoading={isSubmitting}>
            Save Lesson Log
          </Button>
        </form>
      </Card>
    </>
  );
}
