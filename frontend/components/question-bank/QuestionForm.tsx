"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import {
  optionLabels,
  QuestionOptionsEditor,
  type OptionTexts
} from "@/components/question-bank/QuestionOptionsEditor";
import {
  getClassLevels,
  getSubjects,
  getTopics
} from "@/lib/academics";
import { ApiError } from "@/lib/api";
import { getQuestionSources } from "@/lib/questionBank";
import type { ClassLevel, Subject, Topic } from "@/types/academics";
import type {
  Question,
  QuestionDifficulty,
  QuestionOptionLabel,
  QuestionPayload,
  QuestionSource
} from "@/types/questionBank";

const difficultyOptions: Array<{ value: QuestionDifficulty; label: string }> = [
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" }
];

function initialOptionTexts(question?: Question): OptionTexts {
  return optionLabels.reduce((texts, label) => {
    const option = question?.options.find((item) => item.label === label);
    return { ...texts, [label]: option?.text ?? "" };
  }, {} as OptionTexts);
}

function initialCorrectOption(question?: Question): QuestionOptionLabel {
  return (
    question?.options.find((item) => item.is_correct)?.label ??
    "A"
  );
}

type QuestionFormProps = {
  initialQuestion?: Question;
  submitLabel: string;
  cancelHref: string;
  onSubmit: (payload: QuestionPayload) => Promise<Question>;
  onSaved: (question: Question) => void;
};

export function QuestionForm({
  initialQuestion,
  submitLabel,
  cancelHref,
  onSubmit,
  onSaved
}: QuestionFormProps) {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [classLevels, setClassLevels] = useState<ClassLevel[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [sources, setSources] = useState<QuestionSource[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [subjectId, setSubjectId] = useState(
    initialQuestion ? String(initialQuestion.subject) : ""
  );
  const [classLevelId, setClassLevelId] = useState(
    initialQuestion ? String(initialQuestion.class_level) : ""
  );
  const [topicId, setTopicId] = useState(
    initialQuestion ? String(initialQuestion.topic) : ""
  );
  const [sourceId, setSourceId] = useState(
    initialQuestion?.source ? String(initialQuestion.source) : ""
  );
  const [difficulty, setDifficulty] = useState<QuestionDifficulty>(
    initialQuestion?.difficulty ?? "medium"
  );
  const [questionText, setQuestionText] = useState(
    initialQuestion?.question_text ?? ""
  );
  const [explanation, setExplanation] = useState(
    initialQuestion?.explanation ?? ""
  );
  const [optionTexts, setOptionTexts] = useState<OptionTexts>(() =>
    initialOptionTexts(initialQuestion)
  );
  const [correctOption, setCorrectOption] = useState<QuestionOptionLabel>(() =>
    initialCorrectOption(initialQuestion)
  );

  useEffect(() => {
    async function loadOptions() {
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
            : "Unable to load question form options."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadOptions();
  }, []);

  const filteredTopics = useMemo(() => {
    return topics.filter((topic) => {
      const matchesSubject = subjectId ? topic.subject === Number(subjectId) : true;
      const matchesClassLevel = classLevelId
        ? topic.class_level === Number(classLevelId)
        : true;
      return matchesSubject && matchesClassLevel;
    });
  }, [classLevelId, subjectId, topics]);

  function setOptionText(label: QuestionOptionLabel, value: string) {
    setOptionTexts((current) => ({ ...current, [label]: value }));
  }

  function validate() {
    if (!subjectId || !classLevelId || !topicId) {
      return "Subject, class level, and topic are required.";
    }

    if (!questionText.trim()) {
      return "Question text is required.";
    }

    const normalizedOptions = optionLabels.map((label) =>
      optionTexts[label].trim()
    );
    if (normalizedOptions.some((text) => !text)) {
      return "Exactly four option texts are required.";
    }

    if (new Set(normalizedOptions.map((text) => text.toLowerCase())).size !== 4) {
      return "Option texts must be unique.";
    }

    if (!correctOption) {
      return "Select one correct option.";
    }

    return "";
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: QuestionPayload = {
        subject: Number(subjectId),
        class_level: Number(classLevelId),
        topic: Number(topicId),
        source: sourceId ? Number(sourceId) : null,
        question_text: questionText.trim(),
        explanation: explanation.trim(),
        difficulty,
        options: optionLabels.map((label) => ({
          label,
          text: optionTexts[label].trim(),
          is_correct: correctOption === label
        }))
      };
      const savedQuestion = await onSubmit(payload);
      onSaved(savedQuestion);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to save question.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading question form..." />;
  }

  if (error && (!subjects.length || !classLevels.length || !topics.length)) {
    return <EmptyState title="Question form unavailable" description={error} />;
  }

  return (
    <form onSubmit={handleSubmit}>
      {error ? (
        <div className="mb-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <Card>
        <div className="grid gap-4 md:grid-cols-2">
          <Select
            label="Subject"
            value={subjectId}
            required
            options={[
              { value: "", label: "Select subject" },
              ...subjects.map((subject) => ({
                value: String(subject.id),
                label: subject.name
              }))
            ]}
            onChange={(event) => {
              setSubjectId(event.target.value);
              setTopicId("");
            }}
          />
          <Select
            label="Class level"
            value={classLevelId}
            required
            options={[
              { value: "", label: "Select class level" },
              ...classLevels.map((classLevel) => ({
                value: String(classLevel.id),
                label: classLevel.name
              }))
            ]}
            onChange={(event) => {
              setClassLevelId(event.target.value);
              setTopicId("");
            }}
          />
          <Select
            label="Topic"
            value={topicId}
            required
            options={[
              { value: "", label: "Select topic" },
              ...filteredTopics.map((topic) => ({
                value: String(topic.id),
                label: topic.title
              }))
            ]}
            onChange={(event) => setTopicId(event.target.value)}
          />
          <Select
            label="Source"
            value={sourceId}
            options={[
              { value: "", label: "No source" },
              ...sources.map((source) => ({
                value: String(source.id),
                label: source.year ? `${source.name} (${source.year})` : source.name
              }))
            ]}
            onChange={(event) => setSourceId(event.target.value)}
          />
          <Select
            label="Difficulty"
            value={difficulty}
            required
            options={difficultyOptions}
            onChange={(event) =>
              setDifficulty(event.target.value as QuestionDifficulty)
            }
          />
        </div>

        <div className="mt-4 grid gap-4">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-ink">
              Question text
            </span>
            <textarea
              className="min-h-32 w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
              required
              value={questionText}
              onChange={(event) => setQuestionText(event.target.value)}
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-ink">
              Explanation
            </span>
            <textarea
              className="min-h-24 w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
              value={explanation}
              onChange={(event) => setExplanation(event.target.value)}
            />
          </label>
          <QuestionOptionsEditor
            optionTexts={optionTexts}
            correctOption={correctOption}
            onOptionTextChange={setOptionText}
            onCorrectOptionChange={setCorrectOption}
          />
        </div>
      </Card>

      <div className="mt-6 flex flex-wrap gap-2">
        <Button type="submit" isLoading={isSubmitting}>
          {submitLabel}
        </Button>
        <Link href={cancelHref}>
          <Button type="button" variant="secondary">
            Cancel
          </Button>
        </Link>
      </div>
    </form>
  );
}
