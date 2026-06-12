"use client";

import { Suspense } from "react";
import { Loader2 } from "lucide-react";
import { ArenaContent } from "./_components/arena-content";

export function ArenaPageClient() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-background flex items-center justify-center">
          <Loader2 className="size-8 animate-spin text-primary" strokeWidth={1.5} />
        </div>
      }
    >
      <ArenaContent />
    </Suspense>
  );
}
