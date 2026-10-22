import { Fragment } from 'react'

// The API's highlight markers are control characters by design (they never occur in real text).
// oxlint-disable-next-line no-control-regex
const MARKED = /(\u0002[^\u0002\u0003]*\u0003)/
// oxlint-disable-next-line no-control-regex
const STRAY_MARKERS = /[\u0002\u0003]/g

// Renders API snippets whose matches are wrapped in \u0002…\u0003. The text is
// always rendered as text nodes; React builds the <mark> elements, so no
// markup from the API is ever interpreted as HTML.
export function Highlighted({ text }: { text: string }) {
  return (
    <>
      {text.split(MARKED).map((part, i) =>
        part.startsWith('\u0002') ? (
          <mark key={i}>{part.slice(1, -1)}</mark>
        ) : (
          <Fragment key={i}>{part.replace(STRAY_MARKERS, '')}</Fragment>
        ),
      )}
    </>
  )
}
