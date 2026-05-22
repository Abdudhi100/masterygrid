"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { BooleanBadge } from "@/components/admin/BooleanBadge";
import { ResourcePage } from "@/components/admin/ResourcePage";
import type { FormState } from "@/components/admin/ResourceForm";
import { Select } from "@/components/ui/Select";
import { LoadingState } from "@/components/ui/LoadingState";
import {
  createTopic,
  getClassLevels,
  getSubjects,
  getTopics,
  updateTopic
} from "@/lib/academics";
import {
  booleanValue,
  csvFromTags,
  numberValue,
  stringValue,
  tagsFromCsv
} from "@/lib/formPayload";
import type { ClassLevel, Subject, Topic } from "@/types/academics";

const initialValues: FormState = {
  subject: "",
  class_level: "",
  title: "",
  description: "",
  curriculum_tags: "",
  jamb_relevance_level: "medium",
  is_active: true
};

export default function TopicsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [classLevels, setClassLevels] = useState<ClassLevel[]>([]);
  const [subjectFilter, setSubjectFilter] = useState("");
  const [classLevelFilter, setClassLevelFilter] = useState("");
  const [isLoadingOptions, setIsLoadingOptions] = useState(true);

  useEffect(() => {
    async function loadOptions() {
      const [subjectRows, levelRows] = await Promise.all([
        getSubjects(),
        getClassLevels()
      ]);
      setSubjects(subjectRows);
      setClassLevels(levelRows);
      setIsLoadingOptions(false);
    }
    void loadOptions();
  }, []);

  const load = useCallback(async () => {
    const topics = await getTopics();
    return topics.filter((topic) => {
      const matchesSubject = subjectFilter
        ? topic.subject === Number(subjectFilter)
        : true;
      const matchesClassLevel = classLevelFilter
        ? topic.class_level === Number(classLevelFilter)
        : true;
      return matchesSubject && matchesClassLevel;
    });
  }, [classLevelFilter, subjectFilter]);

  const fields = useMemo(
    () => [
      {
        name: "subject",
        label: "Subject",
        type: "select" as const,
        required: true,
        options: subjects.map((subject) => ({
          value: String(subject.id),
          label: subject.name
        }))
      },
      {
        name: "class_level",
        label: "Class level",
        type: "select" as const,
        required: true,
        options: classLevels.map((level) => ({
          value: String(level.id),
          label: level.name
        }))
      },
      { name: "title", label: "Topic title", type: "text" as const, required: true },
      { name: "description", label: "Description", type: "textarea" as const },
      {
        name: "curriculum_tags",
        label: "Curriculum tags",
        type: "text" as const,
        placeholder: "Comma-separated tags"
      },
      {
        name: "jamb_relevance_level",
        label: "JAMB relevance",
        type: "select" as const,
        required: true,
        options: [
          { value: "low", label: "Low" },
          { value: "medium", label: "Medium" },
          { value: "high", label: "High" }
        ]
      },
      { name: "is_active", label: "Active topic", type: "checkbox" as const }
    ],
    [classLevels, subjects]
  );

  if (isLoadingOptions) {
    return <LoadingState label="Loading subjects and class levels..." />;
  }

  return (
    <ResourcePage<Topic>
      title="Topics"
      description="Manage curriculum topics used for lessons, questions, and assignments."
      createLabel="New topic"
      load={load}
      create={(payload) => createTopic(payload)}
      update={(id, payload) => updateTopic(id, payload)}
      initialValues={initialValues}
      toFormValues={(row) => ({
        subject: String(row.subject),
        class_level: String(row.class_level),
        title: row.title,
        description: row.description,
        curriculum_tags: csvFromTags(row.curriculum_tags),
        jamb_relevance_level: row.jamb_relevance_level,
        is_active: row.is_active
      })}
      toPayload={(values) => ({
        subject: numberValue(values.subject),
        class_level: numberValue(values.class_level),
        title: stringValue(values.title),
        description: stringValue(values.description),
        curriculum_tags: tagsFromCsv(values.curriculum_tags),
        jamb_relevance_level: stringValue(values.jamb_relevance_level),
        is_active: booleanValue(values.is_active)
      })}
      fields={fields}
      filters={
        <div className="grid gap-4 md:grid-cols-2">
          <Select
            label="Filter by subject"
            value={subjectFilter}
            options={[
              { value: "", label: "All subjects" },
              ...subjects.map((subject) => ({
                value: String(subject.id),
                label: subject.name
              }))
            ]}
            onChange={(event) => setSubjectFilter(event.target.value)}
          />
          <Select
            label="Filter by class level"
            value={classLevelFilter}
            options={[
              { value: "", label: "All class levels" },
              ...classLevels.map((level) => ({
                value: String(level.id),
                label: level.name
              }))
            ]}
            onChange={(event) => setClassLevelFilter(event.target.value)}
          />
        </div>
      }
      columns={[
        { key: "title", header: "Topic", render: (row) => row.title },
        {
          key: "subject",
          header: "Subject",
          render: (row) => row.subject_name ?? row.subject
        },
        {
          key: "class_level",
          header: "Class level",
          render: (row) => row.class_level_name ?? row.class_level
        },
        {
          key: "jamb_relevance_level",
          header: "JAMB",
          render: (row) => row.jamb_relevance_level
        },
        {
          key: "is_active",
          header: "Status",
          render: (row) => <BooleanBadge value={row.is_active} />
        }
      ]}
    />
  );
}
