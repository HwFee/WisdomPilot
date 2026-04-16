/**
 * Code Templates for Different Languages
 *
 * Provides default code templates and comment styles for each supported language.
 */

export const LANGUAGE_TEMPLATES: Record<string, string> = {
  python: '# 在此编写你的代码\n',
  c: '// 在此编写你的代码\n',
  cpp: '// 在此编写你的代码\n',
  java: '// 在此编写你的代码\n',
  rust: '// 在此编写你的代码\n',
}

export const LANGUAGE_COMMENT_STYLES: Record<string, { line: string; blockStart?: string; blockEnd?: string }> = {
  python: { line: '#' },
  c: { line: '//', blockStart: '/*', blockEnd: '*/' },
  cpp: { line: '//', blockStart: '/*', blockEnd: '*/' },
  java: { line: '//', blockStart: '/*', blockEnd: '*/' },
  rust: { line: '//', blockStart: '/*', blockEnd: '*/' },
}

/**
 * Get template for a language
 */
export function getTemplate(language: string): string {
  return LANGUAGE_TEMPLATES[language] || '// Write your code here\n'
}

/**
 * Get comment style for a language
 */
export function getCommentStyle(language: string): { line: string; blockStart?: string; blockEnd?: string } {
  return LANGUAGE_COMMENT_STYLES[language] || { line: '//' }
}
