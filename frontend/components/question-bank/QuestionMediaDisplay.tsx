"use client";

/* eslint-disable @next/next/no-img-element */

import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import type { QuestionMedia } from "@/types/questionBank";

type QuestionMediaDisplayProps = {
  media?: QuestionMedia[];
  diagramDescription?: string | null;
  hasDiagram?: boolean;
  compact?: boolean;
};

function mediaUrl(item: QuestionMedia) {
  return item.image_url || item.external_url || item.image || "";
}

function sortedMedia(media: QuestionMedia[]) {
  return [...media]
    .filter((item) => item.is_active !== false)
    .sort((first, second) => {
      if (first.is_primary !== second.is_primary) {
        return first.is_primary ? -1 : 1;
      }
      return first.display_order - second.display_order;
    });
}

function QuestionMediaItem({
  item,
  compact
}: {
  item: QuestionMedia;
  compact?: boolean;
}) {
  const [hasImageError, setHasImageError] = useState(false);
  const url = mediaUrl(item);
  const description = item.caption || item.description || item.alt_text;

  return (
    <figure className="rounded-md border border-line bg-surface p-3">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <Badge tone="brand">Diagram</Badge>
        {item.needs_manual_review ? (
          <Badge tone="warning">Needs manual review</Badge>
        ) : null}
        {item.is_primary ? <Badge tone="success">Primary</Badge> : null}
      </div>

      {url && !hasImageError ? (
        <img
          src={url}
          alt={item.alt_text || item.description || item.caption || "Question diagram"}
          className={`w-full rounded-md border border-line bg-white object-contain ${
            compact ? "max-h-56" : "max-h-[32rem]"
          }`}
          loading="lazy"
          onError={() => setHasImageError(true)}
        />
      ) : (
        <div className="flex min-h-32 items-center justify-center rounded-md border border-dashed border-line bg-white px-4 py-8 text-center text-sm text-muted">
          Diagram image could not be loaded.
        </div>
      )}

      {description ? (
        <figcaption className="mt-2 text-sm leading-6 text-muted">
          {description}
        </figcaption>
      ) : null}
    </figure>
  );
}

export function QuestionMediaDisplay({
  media = [],
  diagramDescription,
  hasDiagram = false,
  compact = false
}: QuestionMediaDisplayProps) {
  const visibleMedia = sortedMedia(media);

  if (!visibleMedia.length && !hasDiagram) {
    return null;
  }

  return (
    <div className="space-y-3">
      {!visibleMedia.length ? (
        <div className="rounded-md border border-amber-100 bg-amber-50 px-4 py-3 text-sm leading-6 text-warning">
          This question is marked as having a diagram, but no image URL is attached
          yet.
          {diagramDescription ? (
            <span className="mt-1 block">{diagramDescription}</span>
          ) : null}
        </div>
      ) : (
        visibleMedia.map((item) => (
          <QuestionMediaItem key={item.id} item={item} compact={compact} />
        ))
      )}
    </div>
  );
}
