export type Session = { user: { name: string; email: string; picture: string } | null; is_admin: boolean; csrf: string; login_enabled: boolean }
export type Post = { title: string; slug: string; date: string; summary: string; published: boolean; body: string; revision?: string; reading_time?: number }
export type Repo = { id: number; name: string; description: string | null; language: string | null; stargazers_count: number; updated_at: string; html_url: string; homepage: string | null; fork: boolean }
export type Saved = { revision?: string; commit_url: string | null }
