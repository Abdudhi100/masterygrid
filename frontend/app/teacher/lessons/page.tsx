"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { Badge } from "@/components/ui/Badge";
import { ApiError } from "@/lib/api";
import { getLessonLogs } from "@/lib/academics";
import type { LessonLog } from "@/types/academics";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function notesPreview(notes: string) {
  if (!notes) {
    return "No notes added";
  }

  return notes.length > 120 ? `${notes.slice(0, 120)}...` : notes;
}

export default function TeacherLessonsPage() {
  const [lessons, setLessons] = useState<LessonLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadLessons() {
      try {
        setLessons(await getLessonLogs());
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Unable to load lessons.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadLessons();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading lesson logs..." />;
  }

  if (error) {
    return <EmptyState title="Lessons unavailable" description={error} />;
  }

  return (
    <>
      <PageHeader
        title="Lessons"
        description="Log taught topics and turn them into topic-based assignments."
        actions={
          <Link href="/teacher/lessons/new">
            <Button>Log New Lesson</Button>
          </Link>
        }
      />

      {lessons.length ? (
        <div className="space-y-4">
          {lessons.map((lesson) => (
            <Card key={lesson.id}>
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-semibold text-ink">
                      {lesson.topic_title ?? "Lesson topic"}
                    </h2>
                    {lesson.can_generate_assignment ? (
                      <Badge tone="success">assignment ready</Badge>
                    ) : null}
                  </div>
                  <p className="mt-2 text-sm font-medium text-muted">
                    {formatDate(lesson.taught_at)} ·{" "}
                    {lesson.class_arm_name ?? "Class arm"} ·{" "}
                    {lesson.subject_name ?? "Subject"}
                  </p>
                  <p className="mt-3 text-sm leading-6 text-muted">
                    {notesPreview(lesson.notes)}
                  </p>
                </div>
                <Link href={`/teacher/assignments/new?lessonLogId=${lesson.id}`}>
                  <Button variant="secondary">Generate Assignment</Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No lessons logged yet"
          description="Log your first taught topic so MasteryGrid can generate assignments from it later."
        />
      )}
    </>
  );
}
