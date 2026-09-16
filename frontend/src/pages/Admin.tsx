import { useEffect, useState, type FormEvent } from 'react'
import { Link, Navigate, Outlet, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowUpRight, FilePlus2, Pencil, Save, Trash2 } from 'lucide-react'
import { useAuth } from '../components/Auth'
import { useApi } from '../hooks/useApi'
import { api, safeUrl } from '../services/api'
import Markdown from '../components/Markdown'
import State from '../components/State'
import { Heading } from './Public'
import type { Post, Saved } from '../types'
export function AdminGuard() {
  const { session, error, refresh } = useAuth()
  if (error) return <State error={error} retry={() => void refresh()}/>
  if (!session) return <State/>
  if (!session.user) return <Navigate to="/login" replace/>
  if (!session.is_admin) return <div className="panel state"><h1>Private workspace</h1><p>This area is available only to the site administrator.</p><Link to="/projects">Explore projects</Link></div>
  return <Outlet/>
}
function Result({ result }: { result?: Saved }) { return result ? <p role="status" className="success">Saved successfully. {result.commit_url ? <a href={safeUrl(result.commit_url)} target="_blank" rel="noreferrer">View GitHub commit <ArrowUpRight size={14}/></a> : 'Local content updated.'}</p> : null }
export function AdminDashboard() {
  const { data, error, reload } = useApi<Post[]>('/admin/blog')
  const [actionError, setActionError] = useState(''), [busy, setBusy] = useState(false), [result, setResult] = useState<Saved>()
  async function remove(post: Post) {
    if (!window.confirm(`Delete “${post.title}”? This removes its Markdown file.`)) return
    setBusy(true); setActionError('')
    try { setResult(await api<Saved>(`/admin/blog/${post.slug}?revision=${encodeURIComponent(post.revision || '')}`, 'DELETE')); reload() } catch(e) { setActionError((e as Error).message) } finally { setBusy(false) }
  }
  return <><Heading eyebrow="PRIVATE WORKSPACE" title="Content studio" text="A small space to write, edit, and share."/><div className="admin-actions"><Link className="primary-button" to="/admin/blog/new"><FilePlus2 size={17}/>New blog post</Link><Link className="outline-link" to="/admin/about"><Pencil size={16}/>Edit about me</Link></div><Result result={result}/>{actionError && <p role="alert" className="notice">{actionError}</p>}{data ? <div className="panel admin-list">{data.length ? data.map(post => <div className="admin-row" key={post.slug}><div><span className={`status ${post.published ? 'published' : ''}`}>{post.published ? 'Published' : 'Draft'}</span><h2>{post.title}</h2><p>{post.date} / {post.slug}</p></div><div className="row-actions"><Link className="icon-button" to={`/admin/blog/${post.slug}/edit`} aria-label={`Edit ${post.title}`}><Pencil size={18}/></Link><button disabled={busy} className="icon-button" onClick={() => void remove(post)} aria-label={`Delete ${post.title}`}><Trash2 size={18}/></button></div></div>) : <p>No posts yet. Create your first one.</p>}</div> : <State error={error} retry={reload}/>}</>
}
const blank = (): Post => ({ title: '', slug: '', date: new Date().toISOString().slice(0, 10), summary: '', published: false, body: '' })
export function BlogEditor() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const [post, setPost] = useState<Post>(blank), [loaded, setLoaded] = useState(!slug), [error, setError] = useState(''), [busy, setBusy] = useState(false), [preview, setPreview] = useState(false), [result, setResult] = useState<Saved>()
  useEffect(() => { let active = true; if (slug) api<Post>(`/admin/blog/${slug}`).then(p => { if(active) { setPost(p); setLoaded(true) } }).catch(e => { if(active) setError(e.message) }); return () => { active = false } }, [slug])
  async function save(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError(''); setResult(undefined)
    try { const saved = await api<Saved>(slug ? `/admin/blog/${slug}` : '/admin/blog', slug ? 'PUT' : 'POST', post); setPost(p => ({ ...p, revision: saved.revision })); setResult(saved); if (!slug) navigate(`/admin/blog/${post.slug}/edit`, { replace: true }) } catch(e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  if (!loaded) return <State error={error}/>
  return <><Link className="back-link" to="/admin"><ArrowLeft size={16}/>Content studio</Link><Heading eyebrow="WORDS INTO THE WORLD" title={slug ? 'Edit post' : 'New post'} text="Write something worth keeping."/><form className="editor panel" onSubmit={save}><div className="form-grid"><label>Title<input required maxLength={180} value={post.title} onChange={e => setPost({ ...post, title: e.target.value })}/></label><label>Slug<input required pattern="[a-z0-9]+(-[a-z0-9]+)*" maxLength={100} disabled={!!slug} value={post.slug} placeholder="my-first-post" onChange={e => setPost({ ...post, slug: e.target.value })}/></label><label>Date<input type="date" required value={post.date} onChange={e => setPost({ ...post, date: e.target.value })}/></label><label className="checkbox-label"><input type="checkbox" checked={post.published} onChange={e => setPost({ ...post, published: e.target.checked })}/>Published — visible to everyone</label></div><label>Summary<textarea rows={2} maxLength={600} value={post.summary} onChange={e => setPost({ ...post, summary: e.target.value })}/></label><div className="editor-toolbar"><span>MARKDOWN CONTENT</span><button type="button" aria-pressed={preview} onClick={() => setPreview(!preview)}>{preview ? 'Back to editor' : 'Preview'}</button></div>{preview ? <div className="preview"><Markdown body={post.body || '*Nothing written yet.*'}/></div> : <textarea className="code-editor" aria-label="Markdown body" rows={18} maxLength={500000} value={post.body} onChange={e => setPost({ ...post, body: e.target.value })}/>}<div className="editor-bottom"><button className="primary-button" disabled={busy}><Save size={16}/>{busy ? 'Saving…' : post.published ? 'Save & publish' : 'Save draft'}</button>{slug && post.published && <Link className="read-link" to={`/blog/${slug}`}>View post<ArrowUpRight size={16}/></Link>}</div>{error && <p role="alert" className="notice">{error}</p>}<Result result={result}/></form></>
}
export function AboutEditor() {
  const { data, error, reload } = useApi<{ body: string; revision: string }>('/admin/about')
  const [body, setBody] = useState(''), [revision, setRevision] = useState(''), [preview, setPreview] = useState(false), [busy, setBusy] = useState(false), [saveError, setSaveError] = useState(''), [result, setResult] = useState<Saved>()
  useEffect(() => { if (data) { setBody(data.body); setRevision(data.revision) } }, [data])
  async function save(e: FormEvent) { e.preventDefault(); setBusy(true); setSaveError(''); setResult(undefined); try { const saved = await api<Saved>('/admin/about', 'PUT', { body, revision }); setRevision(saved.revision || ''); setResult(saved) } catch(e) { setSaveError((e as Error).message) } finally { setBusy(false) } }
  return <><Link to="/admin" className="back-link"><ArrowLeft size={16}/>Content studio</Link><Heading eyebrow="YOUR STORY" title="Edit about me" text="A few words about the person behind the projects."/>{data ? <form className="editor panel" onSubmit={save}><div className="editor-toolbar"><span>ABOUT / MARKDOWN</span><button type="button" aria-pressed={preview} onClick={() => setPreview(!preview)}>{preview ? 'Edit' : 'Preview'}</button></div>{preview ? <div className="preview"><Markdown body={body}/></div> : <textarea className="code-editor" aria-label="About Markdown" rows={20} maxLength={500000} value={body} onChange={e => setBody(e.target.value)}/>}<button disabled={busy} className="primary-button"><Save size={16}/>{busy ? 'Saving…' : 'Save about page'}</button>{saveError && <p role="alert" className="notice">{saveError}</p>}<Result result={result}/></form> : <State error={error} retry={reload}/>}</>
}
