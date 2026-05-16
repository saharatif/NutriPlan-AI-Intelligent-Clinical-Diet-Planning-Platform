export type AuditLog = { id: string; action: string; metadata_json?: Record<string, unknown> | null };

export default function AuditLogTable({ logs }: { logs: AuditLog[] }) {
  return (
    <div className="data-panel">
      <div className="panel-header"><div><h2>Audit log</h2><span>{logs.length} events</span></div></div>
      <table>
        <thead><tr><th>Event</th><th>Metadata</th></tr></thead>
        <tbody>
          {logs.map((log) => <tr key={log.id}><td>{log.action}</td><td>{JSON.stringify(log.metadata_json ?? {})}</td></tr>)}
          {logs.length === 0 && <tr><td colSpan={2}>No events yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
