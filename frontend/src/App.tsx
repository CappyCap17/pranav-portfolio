import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './components/Auth'
import Layout from './layouts/Layout'
import { Projects, Blog, Article, AboutPage, Contact, Login, NotFound } from './pages/Public'
import { AdminGuard, AdminDashboard, BlogEditor, AboutEditor } from './pages/Admin'
export default function App() { return <BrowserRouter><AuthProvider><Routes><Route element={<Layout/>}><Route index element={<Navigate to="/projects" replace/>}/><Route path="projects" element={<Projects/>}/><Route path="blog" element={<Blog/>}/><Route path="blog/:slug" element={<Article/>}/><Route path="about" element={<AboutPage/>}/><Route path="contact" element={<Contact/>}/><Route path="login" element={<Login/>}/><Route element={<AdminGuard/>}><Route path="admin" element={<AdminDashboard/>}/><Route path="admin/blog/new" element={<BlogEditor/>}/><Route path="admin/blog/:slug/edit" element={<BlogEditor/>}/><Route path="admin/about" element={<AboutEditor/>}/></Route><Route path="*" element={<NotFound/>}/></Route></Routes></AuthProvider></BrowserRouter> }
