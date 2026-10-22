interface BarItem {
  label: string
  value: number
}

// Plain-CSS horizontal bars; widths are relative to the largest value, and the real number is always printed.
export function DistributionBars({ title, items }: { title: string; items: BarItem[] }) {
  const max = Math.max(1, ...items.map((item) => item.value))
  return (
    <section className="distribution" aria-label={title}>
      <h3>{title}</h3>
      {items.length === 0 ? (
        <p className="hint">No data.</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item.label}>
              <span className="distribution__label">{item.label}</span>
              <span className="distribution__track">
                <span className="distribution__bar" style={{ width: `${(item.value / max) * 100}%` }} />
              </span>
              <span className="distribution__value">{item.value}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
