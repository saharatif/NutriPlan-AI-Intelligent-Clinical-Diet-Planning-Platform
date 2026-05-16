import AllergenBadge from './AllergenBadge';

export type MedicalProfile = {
  conditions: string[];
  allergens: string[];
  medications: string[];
  abnormal_markers: string[];
  medication_rules: string[];
  nutrition_constraints: {
    avoid?: string[];
    limit?: string[];
    prefer?: string[];
  };
};

type MedicalProfileCardProps = {
  profile: MedicalProfile | null;
};

function ChipList({ values }: { values: string[] }) {
  if (!values.length) return <span className="empty-copy">None recorded</span>;
  return <div className="chip-row">{values.map((value) => <span className="profile-chip" key={value}>{value}</span>)}</div>;
}

export default function MedicalProfileCard({ profile }: MedicalProfileCardProps) {
  if (!profile) {
    return (
      <section className="checkout-summary profile-card">
        <div className="panel-header">
          <div>
            <h2>Medical profile</h2>
            <span>Build a profile after OCR or manual intake.</span>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="checkout-summary profile-card">
      <div className="panel-header">
        <div>
          <h2>Medical profile</h2>
          <span>Normalised constraints for plan generation</span>
        </div>
      </div>
      <div className="profile-grid">
        <article>
          <strong>Conditions</strong>
          <ChipList values={profile.conditions} />
        </article>
        <article>
          <strong>Allergens</strong>
          <div className="chip-row">
            {profile.allergens.length ? profile.allergens.map((allergen) => <AllergenBadge key={allergen} name={allergen} />) : <span className="empty-copy">None recorded</span>}
          </div>
        </article>
        <article>
          <strong>Medications</strong>
          <ChipList values={profile.medications} />
        </article>
        <article>
          <strong>Abnormal markers</strong>
          <ChipList values={profile.abnormal_markers} />
        </article>
      </div>
      <div className="constraint-grid">
        <div><span>Avoid</span><ChipList values={profile.nutrition_constraints.avoid ?? []} /></div>
        <div><span>Limit</span><ChipList values={profile.nutrition_constraints.limit ?? []} /></div>
        <div><span>Prefer</span><ChipList values={profile.nutrition_constraints.prefer ?? []} /></div>
      </div>
    </section>
  );
}
