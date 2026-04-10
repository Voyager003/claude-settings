---
name: frontend-patterns
description: Frontend development patterns for React, Next.js, state management, performance optimization, and UI best practices.
---

# Frontend Development Patterns

Modern frontend patterns for React, Next.js, and performant user interfaces.

## When to Activate

- Building React components (composition, props, rendering)
- Managing state (useState, useReducer, Zustand, Context)
- Implementing data fetching (SWR, React Query, server components)
- Optimizing performance (memoization, virtualization, code splitting)
- Working with forms (validation, controlled inputs, Zod schemas)
- Building accessible, responsive UI patterns

## Component Patterns

### Composition Over Inheritance
```typescript
export function Card({ children, variant = 'default' }: CardProps) {
  return <div className={`card card-${variant}`}>{children}</div>
}
```

### Compound Components
Use Context to share implicit state between related components (Tabs, Accordion, etc.).

### Custom Hooks
```typescript
export function useToggle(initialValue = false): [boolean, () => void] {
  const [value, setValue] = useState(initialValue)
  const toggle = useCallback(() => setValue(v => !v), [])
  return [value, toggle]
}

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])
  return debouncedValue
}
```

## State Management

### Context + Reducer Pattern
```typescript
type Action =
  | { type: 'SET_ITEMS'; payload: Item[] }
  | { type: 'SELECT_ITEM'; payload: Item }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_ITEMS': return { ...state, items: action.payload }
    case 'SELECT_ITEM': return { ...state, selected: action.payload }
  }
}
```

## Performance Optimization

- `useMemo` for expensive computations
- `useCallback` for functions passed to children
- `React.memo` for pure components
- `lazy()` + `Suspense` for code splitting
- `@tanstack/react-virtual` for long lists

## Accessibility

- Keyboard navigation (ArrowDown/Up, Enter, Escape)
- Focus management (save/restore focus on modal open/close)
- ARIA roles and attributes (`role`, `aria-expanded`, `aria-modal`)
