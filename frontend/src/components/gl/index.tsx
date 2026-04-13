"use client";

import dynamic from "next/dynamic";
import { useTheme } from "next-themes";

const GLCanvas = dynamic(
  () => import("./gl-canvas").then((mod) => ({ default: mod.GLCanvas })),
  { ssr: false }
);

export function GL() {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <div className="absolute inset-0 w-full h-full pointer-events-none">
      <GLCanvas
        bgColor={isDark ? "#000" : "#fff"}
        particleColor={[0.95, 0.65, 0.3]}
      />
    </div>
  );
}
