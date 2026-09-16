import { useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { ArrowUpRight, BookOpen, FolderGit2, Github, LogIn, LogOut, Mail, Menu, Shield, User, X } from 'lucide-react'
import { site } from '../config/site'
import { useAuth } from '../components/Auth'
import { api } from '../services/api'
const links = [{ to: '/projects', label: 'Projects', icon: FolderGit2 }, { to: '/blog', label: 'Blogs', icon: BookOpen }, { to: '/about', label: 'About Me', icon: User }, { to: '/contact', label: 'Contact', icon: Mail }]
export default function Layout() {
  const [open, setOpen] = useState(false)
  const [error, setError] = useState('')
  const { session, refresh } = useAuth()
  const location = useLocation()
  async function logout() { try { await api('/auth/logout', 'POST'); await refresh() } catch(e) { setError((e as Error).message) } }
  return <div className="dashboard" onKeyDown={e => { if (e.key === 'Escape') setOpen(false) }}>
    <a className="skip-link" href="#main">Skip to content</a>
    {open && <button className="backdrop" aria-label="Close navigation" onClick={() => setOpen(false)}/>}
    <aside className={`sidebar panel ${open ? 'open' : ''}`}>
      <Link to="/projects" className="brand" onClick={() => setOpen(false)}><span className="monogram">py<span>.</span></span><span>PERSONAL SPACE</span></Link>
      <div className="nav-caption">EXPLORE</div>
      <nav aria-label="Main navigation">{links.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} onClick={() => setOpen(false)} className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}><Icon size={19}/>{label}<span className="active-dot"/></NavLink>)}</nav>
      <div className="sidebar-bottom"><a className="github-sidebar" href={site.githubUrl} target="_blank" rel="noreferrer"><Github size={18}/><span>@{site.githubUsername}</span><ArrowUpRight size={15}/></a>
      {session?.is_admin && <NavLink className="nav-link" to="/admin" onClick={() => setOpen(false)}><Shield size={18}/>Admin</NavLink>}
      {session?.user ? <button className="nav-link" onClick={logout}><LogOut size={18}/>Logout</button> : <NavLink className="nav-link" to="/login" onClick={() => setOpen(false)}><LogIn size={18}/>Login</NavLink>}
      {error && <p role="alert">{error}</p>}<div className="sidebar-foot">A little code. A lot of curiosity.</div></div>
    </aside>
    <div className="workspace"><header className="topbar panel"><button className="icon-button mobile-menu" aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open} onClick={() => setOpen(!open)}>{open ? <X size={20}/> : <Menu size={20}/>}</button><Link to="/projects" className="site-name">{site.name}</Link><div className="topbar-right"><span className="personal-label">DEVELOPER / EXPLORER</span><Link to={session?.is_admin ? '/admin' : '/login'} className="account" aria-label="Your account"><User size={19}/></Link></div></header>
    <main id="main" key={location.pathname} tabIndex={-1}><Outlet/></main>
    <footer><span>© {new Date().getFullYear()} {site.name}</span><span>Made with curiosity <span className="footer-dot">✳</span></span></footer></div>
  </div>
}
