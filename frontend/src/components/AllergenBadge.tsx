type AllergenBadgeProps = {
  name: string;
  severity?: string | null;
};

export default function AllergenBadge({ name, severity }: AllergenBadgeProps) {
  const normalized = severity?.toLowerCase() ?? '';
  const className = normalized.includes('anaphyl') || normalized.includes('high')
    ? 'allergen-badge critical'
    : normalized.includes('intoler')
      ? 'allergen-badge warning'
      : 'allergen-badge attention';

  return <span className={className}>{name}</span>;
}
