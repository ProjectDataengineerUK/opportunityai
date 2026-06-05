"use client";

const AREAS = ["IA", "Dados", "Python", "Backend", "Automação", "Cloud", "Irrelevante"];
const DECISIONS = ["APLICAR", "AVALIAR", "IGNORAR"];
const SOURCES = ["freelancer", "workana", "upwork", "remoteok", "remotive"];

interface FilterBarProps {
  area: string;
  decision: string;
  source: string;
  onAreaChange: (v: string) => void;
  onDecisionChange: (v: string) => void;
  onSourceChange: (v: string) => void;
}

function Select({
  value,
  onChange,
  options,
  label,
}: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
  label: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="text-sm border border-input rounded-lg px-3 py-1.5 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring dark:[color-scheme:dark]"
    >
      <option value="all">{label}</option>
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  );
}

export function FilterBar({
  area,
  decision,
  source,
  onAreaChange,
  onDecisionChange,
  onSourceChange,
}: FilterBarProps) {
  return (
    <div className="flex flex-wrap gap-3 items-center">
      <Select value={area} onChange={onAreaChange} options={AREAS} label="Todas as áreas" />
      <Select value={decision} onChange={onDecisionChange} options={DECISIONS} label="Todas as decisões" />
      <Select value={source} onChange={onSourceChange} options={SOURCES} label="Todas as plataformas" />
    </div>
  );
}
