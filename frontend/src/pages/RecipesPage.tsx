import { ChefHat } from 'lucide-react';

export default function RecipesPage() {
  return (
    <div className="content">
      <div className="page-header">
        <div>
          <h1>Custom Recipes</h1>
          <p style={{ color: 'var(--slate)', fontSize: 14, marginTop: 4 }}>
            Build and manage your clinic's recipe library
          </p>
        </div>
      </div>

      <div className="coming-soon-panel">
        <ChefHat size={40} strokeWidth={1.5} color="var(--steel)" />
        <h2>Coming soon</h2>
        <p>
          Custom recipes will let you add your own meal templates to the plan generator —
          ensuring generated plans reflect your clinic's dietary preferences and patient favourites.
        </p>
        <ul className="coming-soon-list">
          <li>Upload or enter custom recipes with full macro breakdown</li>
          <li>Tag recipes by condition, allergen, or meal slot</li>
          <li>Prioritise clinic recipes in AI-generated plans</li>
          <li>Share recipes across your team</li>
        </ul>
      </div>
    </div>
  );
}
