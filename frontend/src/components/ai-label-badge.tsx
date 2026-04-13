"use client";

import type { AIDisclosure, AILabelPosition } from "@/types";

interface AILabelBadgeProps {
  disclosure: AIDisclosure | null;
}

const POSITION_CLASSES: Record<AILabelPosition, string> = {
  TOP_LEFT: "top-2 left-2",
  TOP_RIGHT: "top-2 right-2",
  BOTTOM_LEFT: "bottom-2 left-2",
  BOTTOM_RIGHT: "bottom-2 right-2",
  NONE: "hidden",
};

export function AILabelBadge({ disclosure }: AILabelBadgeProps) {
  if (!disclosure || !disclosure.labeled) {
    return null;
  }

  const positionClass =
    POSITION_CLASSES[disclosure.position] ?? POSITION_CLASSES.BOTTOM_RIGHT;

  return (
    <span
      className={`absolute ${positionClass} z-10 rounded bg-black/60 px-1.5 py-0.5 text-[10px] font-medium leading-tight text-white backdrop-blur-sm`}
    >
      {disclosure.label_text}
    </span>
  );
}
