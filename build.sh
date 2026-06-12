#!/bin/bash
# Wrapper for comet-guard build_command
# Build frontend (Next.js) + verify tsc
cd "$(dirname "$0")/frontend"
pnpm build
