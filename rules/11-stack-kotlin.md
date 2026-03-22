# rules/11-stack-kotlin.md — KOTLIN CODE STYLE

## SUMMARY (READ FIRST)
- Follow idiomatic Kotlin conventions over Java-style patterns.
- Leverage Kotlin features (null safety, extension functions, data classes, sealed classes).
- Same simplicity-first / review-friendly principles as Java/Spring rules.

## RULES
### R1) Kotlin Conventions
- Methods: 30 lines recommended max, cyclomatic complexity 10 or below
- Extension functions: use when they improve readability
- Expression body: use when readability is maintained
- Naming: Class PascalCase, Method camelCase, Constant UPPER_SNAKE_CASE

### R2) Null Safety
- Prefer non-nullable types by default.
- Use `?.let { }` / `?.run { }` over `if (x != null)` when idiomatic.
- Avoid `!!` — use `requireNotNull()` or `checkNotNull()` with clear messages.
- `lateinit` only for DI/framework-injected fields, not for general lazy init.

### R3) Data Classes & Sealed Classes
- Use `data class` for DTOs / value objects.
- Use `sealed class/interface` for restricted type hierarchies (e.g., Result, State).

### R4) Coroutines (if used)
- Use `runTest` in tests (not `runBlocking`).
- Structured concurrency: use `coroutineScope` / `supervisorScope`.
- Never launch unstructured coroutines without explicit scope.

### R5) Collections & Sequences
- Prefer collection functions (`map`, `filter`, `groupBy`) over manual loops.
- Use `Sequence` for large/chained operations (lazy evaluation).

### R6) Interop with Java/Spring
- Use `@JvmStatic`, `@JvmOverloads` when needed for Java interop.
- Spring annotations work the same: `@Service`, `@RestController`, etc.

## EXAMPLES
- BAD: `val name: String? = getName(); if (name != null) { process(name) }`
- GOOD: `getName()?.let { process(it) }`
- BAD: `fun calculate(): Int { return x + y }`
- GOOD: `fun calculate(): Int = x + y`
