#!/bin/bash
# Build frontend (Next.js) + verify tsc
cd "$(dirname "$0")/frontend"
pnpm build
