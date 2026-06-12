"use client";

import { Suspense } from "react";
import { Loader2 } from "lucide-react";
import { MasteryPathContent } from "./_components/mastery-path-content";

export function MasteryPathPageClient() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-background">
          <Loader2 className="size-8 text-primary" strokeWidth={1.5} />
        </div>
      }
    >
      <MasteryPathContent />
    </Suspense>
  );
}
