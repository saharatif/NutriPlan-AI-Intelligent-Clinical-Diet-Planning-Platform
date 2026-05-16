export type BloodTestResult = {
  id: string;
  marker_name: string;
  value: number | null;
  unit: string | null;
  reference_range: string | null;
  is_abnormal: boolean;
};

type OCRResultViewerProps = {
  results: BloodTestResult[];
};

export default function OCRResultViewer({ results }: OCRResultViewerProps) {
  return (
    <div className="data-panel">
      <div className="panel-header">
        <div>
          <h2>Blood markers</h2>
          <span>{results.length} extracted markers</span>
        </div>
      </div>
      <table>
        <thead>
          <tr><th>Marker</th><th>Value</th><th>Reference</th><th>Status</th></tr>
        </thead>
        <tbody>
          {results.map((result) => (
            <tr key={result.id} className={result.is_abnormal ? 'abnormal-row' : undefined}>
              <td>{result.marker_name}</td>
              <td>{result.value ?? '-'} {result.unit}</td>
              <td>{result.reference_range ?? '-'}</td>
              <td>{result.is_abnormal ? 'Abnormal' : 'Normal'}</td>
            </tr>
          ))}
          {results.length === 0 && <tr><td colSpan={4}>No blood markers yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
