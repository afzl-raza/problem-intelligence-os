import { useEffect, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { suggest } from '../api/client'
import type { Suggestion } from '../api/types'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  onSearch: (query: string) => void
  isLoading: boolean
}

const DEBOUNCE_MS = 200
const LISTBOX_ID = 'search-suggestions'

export function SearchBar({ value, onChange, onSearch, isLoading }: SearchBarProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  // Only user typing opens the dropdown; programmatic value changes (a picked
  // suggestion, "did you mean") must not pop it back open.
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)

  const canSuggest = open && value.trim().length >= 2

  useEffect(() => {
    const trimmed = value.trim()
    if (!open || trimmed.length < 2) return
    const controller = new AbortController()
    const timer = setTimeout(() => {
      suggest(trimmed, controller.signal)
        // Domains get their own browse view in a later sprint; offer problems and companies here.
        .then((results) => setSuggestions(results.filter((s) => s.kind !== 'domain')))
        .catch(() => setSuggestions([]))
    }, DEBOUNCE_MS)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [value, open])

  function close() {
    setOpen(false)
    setActiveIndex(-1)
  }

  function submit(query: string) {
    const trimmed = query.trim()
    if (!trimmed) return
    close()
    onSearch(trimmed)
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    submit(value)
  }

  function pick(suggestion: Suggestion) {
    onChange(suggestion.label)
    submit(suggestion.label)
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    const showing = canSuggest && suggestions.length > 0
    if (event.key === 'ArrowDown' && showing) {
      event.preventDefault()
      setActiveIndex((i) => (i + 1) % suggestions.length)
    } else if (event.key === 'ArrowUp' && showing) {
      event.preventDefault()
      setActiveIndex((i) => (i <= 0 ? suggestions.length - 1 : i - 1))
    } else if (event.key === 'Enter' && showing && activeIndex >= 0) {
      event.preventDefault()
      pick(suggestions[activeIndex])
    } else if (event.key === 'Escape') {
      close()
    }
  }

  const showSuggestions = canSuggest && suggestions.length > 0

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <div className="search-bar__field">
        <input
          type="text"
          value={value}
          onChange={(event) => {
            onChange(event.target.value)
            setOpen(true)
            setActiveIndex(-1)
          }}
          onKeyDown={handleKeyDown}
          onBlur={close}
          placeholder='Describe a problem, e.g. parking enforcement — try "phrases", OR, -exclude'
          aria-label="Search problems"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={showSuggestions}
          aria-controls={LISTBOX_ID}
          aria-activedescendant={activeIndex >= 0 ? `suggestion-${activeIndex}` : undefined}
        />
        {showSuggestions && (
          <ul className="suggestions" id={LISTBOX_ID} role="listbox">
            {suggestions.map((suggestion, i) => (
              <li
                key={`${suggestion.kind}-${suggestion.value}`}
                id={`suggestion-${i}`}
                role="option"
                aria-selected={i === activeIndex}
                className={`suggestions__item ${i === activeIndex ? 'suggestions__item--active' : ''}`}
                // mousedown + preventDefault keeps the input focused so blur doesn't close the list first.
                onMouseDown={(event) => {
                  event.preventDefault()
                  pick(suggestion)
                }}
              >
                <span className="suggestions__kind">{suggestion.kind}</span>
                {suggestion.label}
              </li>
            ))}
          </ul>
        )}
      </div>
      <button type="submit" disabled={isLoading || value.trim().length === 0}>
        {isLoading ? 'Searching…' : 'Search'}
      </button>
    </form>
  )
}
