# Domain Glossary

## Core Concepts

### Knowledge Point (知识点)
The smallest teachable unit within a section. Each knowledge point contains:
- `name`: title of the concept
- `content`: explanation text (markdown)
- `code_example`: optional runnable code snippet
- `code_language`: programming language of the example (e.g. 'python', 'c')
- `difficulty`: 1-5 scale

### Section Learning Page (小节学习页)
The page where students read knowledge points before taking the base quiz. URL pattern:
`/mastery/{courseId}/chapter/{chapterId}/section/{sectionId}`.

### Code Runner (代码运行器)
An embedded code editor + execution component within the section learning page.
- Allows students to edit and run code to see output
- **Not a debugger** — no breakpoints, step-through, or variable inspection
- Pre-fills with the knowledge point's `code_example` by default
- Supports language switching (Python / C / C++ / JavaScript / TypeScript)
- Each knowledge point maintains independent editor state in memory
- Output is transient — only code and language selection persist across knowledge point switches

## UI Layout

### Split View (分栏模式)
Triggered when a student clicks "在线运行" on a knowledge point:
- Left: knowledge point list (narrow, ~40%)
- Right: code runner (wide, ~60%)
- A collapse button restores single-column browsing mode

### Single Column (单栏模式)
Default layout — knowledge points stacked vertically, no code runner visible.
