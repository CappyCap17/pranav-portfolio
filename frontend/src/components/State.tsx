export default function State({ error, retry }: { error?: string; retry?: () => void }) {
  return <div className="panel state" role={error ? 'alert' : 'status'}>{error ? <><h3>Something didn’t load</h3><p>{error}</p>{retry && <button onClick={retry}>Try again</button>}</> : <><span className="loading-dot"/> Loading…</>}</div>
}
