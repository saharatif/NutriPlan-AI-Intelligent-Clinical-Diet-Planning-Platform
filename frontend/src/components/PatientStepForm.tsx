import { Trash2, Upload, X } from 'lucide-react';
import { useRef, useState } from 'react';
import type { PatientPayload } from '../store/usePatientStore';

const STEPS = ['Basic Info', 'Conditions', 'Medications', 'Allergens', 'Family History', 'Favourite Foods', 'Documents'];

type Props = {
  onSubmit: (payload: PatientPayload, files: File[]) => Promise<void>;
};

function ChipList<T>({ items, label, onRemove }: { items: T[]; label: (item: T) => string; onRemove: (i: number) => void }) {
  if (!items.length) return <p className="empty-copy">None added yet.</p>;
  return (
    <div className="chip-row">
      {items.map((item, i) => (
        <span key={i} className="chip-item">
          {label(item)}
          <button type="button" className="chip-remove" onClick={() => onRemove(i)} aria-label="Remove">
            <X size={12} />
          </button>
        </span>
      ))}
    </div>
  );
}

export default function PatientStepForm({ onSubmit }: Props) {
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  // Step 0 — Basic info
  const [firstName, setFirstName]   = useState('');
  const [lastName,  setLastName]    = useState('');
  const [dob,       setDob]         = useState('');
  const [sex,       setSex]         = useState<'male' | 'female' | 'other' | ''>('');
  const [heightCm,  setHeightCm]    = useState('');
  const [weightKg,  setWeightKg]    = useState('');
  const [notes,     setNotes]       = useState('');

  // Step 1 — Conditions
  const [condInput,    setCondInput]   = useState('');
  const [conditions,   setConditions]  = useState<Array<{ name: string }>>([]);

  // Step 2 — Medications
  const [medInput,    setMedInput]   = useState('');
  const [medDosage,   setMedDosage]  = useState('');
  const [medications, setMedications] = useState<Array<{ name: string; dosage?: string }>>([]);

  // Step 3 — Allergens
  const [allergenInput,   setAllergenInput]  = useState('');
  const [allergenSev,     setAllergenSev]    = useState<'intolerance' | 'allergy' | 'anaphylactic'>('allergy');
  const [allergens,       setAllergens]       = useState<Array<{ name: string; severity: string }>>([]);

  // Step 4 — Family history
  const [famCondition,    setFamCondition]    = useState('');
  const [famRelation,     setFamRelation]     = useState('');
  const [familyHistory,   setFamilyHistory]   = useState<Array<{ condition: string; relationship: string }>>([]);

  // Step 5 — Favourite foods
  const [foodInput,       setFoodInput]       = useState('');
  const [favouriteFoods,  setFavouriteFoods]  = useState<Array<{ name: string; preference_level: number }>>([]);

  // Step 6 — Documents
  const [files, setFiles]   = useState<File[]>([]);
  const fileRef             = useRef<HTMLInputElement>(null);

  // ── helpers ──────────────────────────────────────────────────────────────
  function addCondition() {
    const name = condInput.trim();
    if (!name) return;
    setConditions([...conditions, { name }]);
    setCondInput('');
  }

  function addMedication() {
    const name = medInput.trim();
    if (!name) return;
    setMedications([...medications, { name, dosage: medDosage.trim() || undefined }]);
    setMedInput(''); setMedDosage('');
  }

  function addAllergen() {
    const name = allergenInput.trim();
    if (!name) return;
    setAllergens([...allergens, { name, severity: allergenSev }]);
    setAllergenInput('');
  }

  function addFamilyHistory() {
    const condition = famCondition.trim();
    if (!condition) return;
    setFamilyHistory([...familyHistory, { condition, relationship: famRelation.trim() }]);
    setFamCondition(''); setFamRelation('');
  }

  function addFood() {
    const name = foodInput.trim();
    if (!name) return;
    setFavouriteFoods([...favouriteFoods, { name, preference_level: 5 }]);
    setFoodInput('');
  }

  function addFiles(incoming: FileList | null) {
    if (!incoming) return;
    const pdfs = Array.from(incoming).filter((f) => f.type === 'application/pdf');
    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name));
      return [...prev, ...pdfs.filter((f) => !existing.has(f.name))];
    });
  }

  // ── submit ────────────────────────────────────────────────────────────────
  async function handleSubmit() {
    if (!firstName || !lastName) { setStep(0); return; }
    setSubmitting(true);
    try {
      const payload: PatientPayload = {
        first_name: firstName,
        last_name:  lastName,
        ...(dob        ? { date_of_birth: dob }          : {}),
        ...(sex        ? { sex }                           : {}),
        ...(heightCm   ? { height_cm: Number(heightCm) }  : {}),
        ...(weightKg   ? { weight_kg: Number(weightKg) }  : {}),
        ...(notes      ? { notes }                         : {}),
        conditions:     conditions,
        medications:    medications,
        allergens:      allergens,
        family_history: familyHistory,
        favourite_foods: favouriteFoods,
      };
      await onSubmit(payload, files);
    } finally {
      setSubmitting(false);
    }
  }

  // ── step content ──────────────────────────────────────────────────────────
  const stepContent = [
    /* 0 — Basic Info */
    <div key="basic" className="form-grid">
      <div className="field-pair">
        <label>First name *<input required value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Mina" /></label>
        <label>Last name *<input required value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Patel" /></label>
      </div>
      <div className="field-pair three">
        <label>Date of birth<input type="date" value={dob} onChange={(e) => setDob(e.target.value)} /></label>
        <label>Height (cm)<input type="number" min="1" value={heightCm} onChange={(e) => setHeightCm(e.target.value)} placeholder="164" /></label>
        <label>Weight (kg)<input type="number" min="1" value={weightKg} onChange={(e) => setWeightKg(e.target.value)} placeholder="68" /></label>
      </div>
      <div>
        <div className="section-kicker" style={{ marginBottom: 8 }}>Sex</div>
        <div className="radio-row">
          {(['female','male','other'] as const).map((s) => (
            <button key={s} type="button" className={sex === s ? 'radio-option selected' : 'radio-option'} onClick={() => setSex(s)}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>
      <label>Clinical notes<textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Any additional clinical context…" style={{ height: 80, resize: 'vertical', padding: '10px 12px' }} /></label>
    </div>,

    /* 1 — Conditions */
    <div key="conditions" className="form-grid">
      <div className="add-row">
        <input value={condInput} onChange={(e) => setCondInput(e.target.value)} placeholder="e.g. Hypertension, Type 2 Diabetes…"
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addCondition(); } }} />
        <button type="button" className="button-primary" onClick={addCondition}>Add</button>
      </div>
      <ChipList items={conditions} label={(c) => c.name} onRemove={(i) => setConditions(conditions.filter((_, j) => j !== i))} />
    </div>,

    /* 2 — Medications */
    <div key="meds" className="form-grid">
      <div className="field-pair">
        <label>Medication name<input value={medInput} onChange={(e) => setMedInput(e.target.value)} placeholder="Metformin"
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addMedication(); } }} /></label>
        <label>Dosage (optional)<input value={medDosage} onChange={(e) => setMedDosage(e.target.value)} placeholder="500 mg twice daily" /></label>
      </div>
      <button type="button" className="button-ghost" onClick={addMedication}>+ Add medication</button>
      <ChipList items={medications} label={(m) => m.dosage ? `${m.name} — ${m.dosage}` : m.name} onRemove={(i) => setMedications(medications.filter((_, j) => j !== i))} />
    </div>,

    /* 3 — Allergens */
    <div key="allergens" className="form-grid">
      <div className="field-pair">
        <label>Allergen<input value={allergenInput} onChange={(e) => setAllergenInput(e.target.value)} placeholder="Milk, Peanuts, Shellfish…"
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addAllergen(); } }} /></label>
        <label>Severity
          <select value={allergenSev} onChange={(e) => setAllergenSev(e.target.value as typeof allergenSev)}>
            <option value="intolerance">Intolerance</option>
            <option value="allergy">Allergy</option>
            <option value="anaphylactic">Anaphylactic</option>
          </select>
        </label>
      </div>
      <button type="button" className="button-ghost" onClick={addAllergen}>+ Add allergen</button>
      <ChipList
        items={allergens}
        label={(a) => `${a.name} (${a.severity})`}
        onRemove={(i) => setAllergens(allergens.filter((_, j) => j !== i))}
      />
    </div>,

    /* 4 — Family History */
    <div key="family" className="form-grid">
      <div className="field-pair">
        <label>Condition<input value={famCondition} onChange={(e) => setFamCondition(e.target.value)} placeholder="Hypertension, Diabetes…" /></label>
        <label>Relation<input value={famRelation} onChange={(e) => setFamRelation(e.target.value)} placeholder="Father, Mother, Sibling…" /></label>
      </div>
      <button type="button" className="button-ghost" onClick={addFamilyHistory}>+ Add entry</button>
      <ChipList
        items={familyHistory}
        label={(f) => f.relationship ? `${f.condition} — ${f.relationship}` : f.condition}
        onRemove={(i) => setFamilyHistory(familyHistory.filter((_, j) => j !== i))}
      />
    </div>,

    /* 5 — Favourite Foods */
    <div key="foods" className="form-grid">
      <div className="add-row">
        <input value={foodInput} onChange={(e) => setFoodInput(e.target.value)} placeholder="Dal, Oatmeal, Salmon…"
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addFood(); } }} />
        <button type="button" className="button-primary" onClick={addFood}>Add</button>
      </div>
      <p className="empty-copy">Add 20–25 foods the patient enjoys. These are used when selecting dishes for diet plan generation.</p>
      <ChipList items={favouriteFoods} label={(f) => f.name} onRemove={(i) => setFavouriteFoods(favouriteFoods.filter((_, j) => j !== i))} />
    </div>,

    /* 6 — Documents */
    <div key="docs" className="form-grid">
      <div
        className="upload-zone"
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); addFiles(e.dataTransfer.files); }}
      >
        <Upload size={28} style={{ color: 'var(--primary)', margin: '0 auto' }} />
        <strong>Drop blood-test PDFs here</strong>
        <span>or click to browse — PDF only, up to 10 MB each</span>
        <input ref={fileRef} type="file" accept="application/pdf" multiple style={{ display: 'none' }}
          onChange={(e) => addFiles(e.target.files)} />
      </div>
      {files.length > 0 && (
        <div className="file-list">
          {files.map((file, i) => (
            <div key={i} className="file-item">
              <span>{file.name}</span>
              <span style={{ color: 'var(--slate)' }}>{(file.size / 1024).toFixed(0)} KB</span>
              <button type="button" className="button-ghost" style={{ minHeight: 32, padding: '0 10px' }}
                onClick={() => setFiles(files.filter((_, j) => j !== i))}>
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
      )}
      <p className="empty-copy">PDFs will be processed immediately after saving. Mistral OCR will extract blood markers, allergens, and conditions, and all content will be embedded into the vector database.</p>
    </div>,
  ];

  return (
    <div className="checkout-summary form-grid">
      {/* Step indicator */}
      <div className="wizard-steps">
        {STEPS.map((label, i) => (
          <button key={label} type="button"
            className={i === step ? 'pill-tab active' : 'pill-tab'}
            onClick={() => setStep(i)}>
            <span className="step-num">{i + 1}</span> {label}
          </button>
        ))}
      </div>

      <div className="step-heading">
        <h3>{STEPS[step]}</h3>
        <span className="empty-copy">Step {step + 1} of {STEPS.length}</span>
      </div>

      {stepContent[step]}

      <div className="button-row">
        {step > 0 && (
          <button type="button" className="button-ghost" onClick={() => setStep(step - 1)}>Back</button>
        )}
        {step < STEPS.length - 1 ? (
          <button type="button" className="button-primary" onClick={() => setStep(step + 1)}>Next →</button>
        ) : (
          <button type="button" className="button-primary" disabled={submitting} onClick={() => void handleSubmit()}>
            {submitting ? 'Saving patient…' : `Save patient${files.length ? ` + ${files.length} PDF${files.length > 1 ? 's' : ''}` : ''}`}
          </button>
        )}
      </div>
    </div>
  );
}
