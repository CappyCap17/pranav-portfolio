import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
export default function Markdown({ body }: { body: string }) {
  return <div className="markdown"><ReactMarkdown remarkPlugins={[remarkGfm]} components={{ a: props => <a {...props} rel="noopener noreferrer"/>, img: props => <img {...props} loading="lazy" alt={props.alt || ''}/> }}>{body}</ReactMarkdown></div>
}
