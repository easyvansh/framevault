export function Alert({ title, children, action }) {
  return <div className="panel p-5" role="alert"><strong className="block text-stone-100">{title}</strong>{children && <p className="mt-2 text-sm text-stone-400">{children}</p>}{action && <div className="mt-4">{action}</div>}</div>;
}
