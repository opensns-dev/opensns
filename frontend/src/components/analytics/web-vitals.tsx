"use client";

import { useEffect } from "react";

type MetricName = "CLS" | "FID" | "FCP" | "LCP" | "TTFB" | "INP";

type MetricPayload = {
  name: MetricName;
  value: number;
  id: string;
};

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }
}

function sendToGa4({ name, value, id }: MetricPayload) {
  if (typeof window === "undefined" || typeof window.gtag !== "function") {
    return;
  }

  window.gtag("event", name, {
    event_category: "Web Vitals",
    event_label: id,
    value: Math.round(name === "CLS" ? value * 1000 : value),
    non_interaction: true,
    metric_id: id,
    metric_name: name,
  });
}

function createObserver(
  type: string,
  callback: PerformanceObserverCallback,
  options?: PerformanceObserverInit & { durationThreshold?: number },
) {
  try {
    const observer = new PerformanceObserver(callback);
    const observeOptions = { type, buffered: true, ...options } as PerformanceObserverInit & {
      durationThreshold?: number;
    };
    observer.observe(observeOptions as PerformanceObserverInit);
    return observer;
  } catch {
    return null;
  }
}

type LayoutShiftEntry = PerformanceEntry & {
  hadRecentInput?: boolean;
  value: number;
};

function trackCls() {
  let cls = 0;
  return createObserver("layout-shift", (list) => {
    for (const entry of list.getEntries() as LayoutShiftEntry[]) {
      if (!entry.hadRecentInput) {
        cls += entry.value;
      }
    }

    sendToGa4({ name: "CLS", value: cls, id: `cls-${performance.now()}` });
  });
}

function trackFcp() {
  return createObserver("paint", (list) => {
    const entry = list.getEntries().find((item) => item.name === "first-contentful-paint");
    if (!entry) {
      return;
    }

    sendToGa4({ name: "FCP", value: entry.startTime, id: `${entry.name}-${entry.startTime}` });
  });
}

function trackLcp() {
  let latestEntry: LargestContentfulPaint | null = null;
  const observer = createObserver("largest-contentful-paint", (list) => {
    const entries = list.getEntries() as LargestContentfulPaint[];
    latestEntry = entries[entries.length - 1] ?? latestEntry;
  });

  const report = () => {
    if (!latestEntry) {
      return;
    }

    sendToGa4({
      name: "LCP",
      value: latestEntry.renderTime || latestEntry.loadTime || latestEntry.startTime,
      id: `${latestEntry.id || "lcp"}-${latestEntry.startTime}`,
    });
  };

  if (observer) {
    window.addEventListener("pagehide", report, { once: true });
  }

  return { observer, report };
}

function trackFirstInput() {
  return createObserver("first-input", (list) => {
    const entry = list.getEntries()[0] as PerformanceEventTiming | undefined;
    if (!entry) {
      return;
    }

    const value = (entry.processingStart ?? 0) - (entry.startTime ?? 0);
    sendToGa4({ name: "FID", value, id: `${entry.name || "fid"}-${entry.startTime}` });
  });
}

function trackInp() {
  let maxDuration = 0;
  let maxEntry: PerformanceEventTiming | null = null;
  const observer = createObserver("event", (list) => {
    for (const entry of list.getEntries() as PerformanceEventTiming[]) {
      if ((entry.duration ?? 0) > maxDuration) {
        maxDuration = entry.duration ?? 0;
        maxEntry = entry;
      }
    }
  }, { durationThreshold: 40 });

  const report = () => {
    if (!maxEntry) {
      return;
    }

    sendToGa4({
      name: "INP",
      value: maxDuration,
      id: `${maxEntry.name || "inp"}-${maxEntry.startTime}`,
    });
  };

  if (observer) {
    window.addEventListener("pagehide", report, { once: true });
  }

  return { observer, report };
}

function trackTtfb() {
  try {
    const navigationEntry = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
    if (!navigationEntry) {
      return;
    }

    sendToGa4({
      name: "TTFB",
      value: navigationEntry.responseStart - navigationEntry.startTime,
      id: `ttfb-${navigationEntry.startTime}`,
    });
  } catch {
    // Ignore unsupported browsers.
  }
}

export function WebVitals() {
  const measurementId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;

  useEffect(() => {
    if (!measurementId) {
      return;
    }

    trackTtfb();
    const fcpObserver = trackFcp();
    const clsObserver = trackCls();
    const fidObserver = trackFirstInput();
    const inpObserver = trackInp();
    const lcpObserver = trackLcp();

    return () => {
      fcpObserver?.disconnect();
      clsObserver?.disconnect();
      fidObserver?.disconnect();
      inpObserver?.observer?.disconnect();
      inpObserver?.report();
      lcpObserver?.observer?.disconnect();
      lcpObserver?.report();
    };
  }, [measurementId]);

  return null;
}
