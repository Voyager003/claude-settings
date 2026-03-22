# rules/10-stack-java-spring.md — JAVA / SPRING BOOT

## SUMMARY (READ FIRST)
- Simplicity first (KISS/YAGNI): no unnecessary abstraction/generalization.
- Review-friendly diffs: do not mix functional changes with formatting/renaming.
- Follow Spring Boot conventions (Controller-Service-Repository layering).
- New dependencies only "when truly needed" + license check included.

## RULES
### R1) Simple-first
- Given same functionality, prefer the simpler design.
- Only increase complexity with evidence (profiling/requirements).

### R2) Naming
- Classes: PascalCase (`UserService`, `OrderController`)
- Methods: camelCase, `verb + noun` (e.g., `fetchUser`, `validateToken`)
- Constants: UPPER_SNAKE_CASE
- Packages: lowercase, dot-separated
- Boolean: `is/has/can/should` prefix

### R3) Spring Boot Patterns
- Layering: Controller → Service → Repository
- Constructor injection (not field injection)
- `@Transactional` at service layer
- Use `@Valid` / `@Validated` for request validation
- Profile-based configuration: `application-{profile}.yml`

### R4) Functions / Methods
- Single responsibility (SRP)
- 30-50+ lines → split candidate
- Nesting depth 3+ → simplification candidate
- 5+ branches → structuring candidate (strategy/table-driven)

### R5) Error Handling / Logging
- Empty catch/ignore prohibited (do not swallow failures).
- Token/password/session/cookie/PII logging prohibited.
- Use SLF4J (`@Slf4j`) for logging, not `System.out`.
- No infinite duplicate error output in loops.

### R6) Library Policy + License
- If solvable with standard library / Spring ecosystem, do not add new dependencies.
- New dependency must include: why needed / alternatives / risks / exit plan / license summary.
- Allowed: MIT / Apache-2.0 / BSD / ISC
- Conditional (approval needed): MPL / EPL / CDDL
- Prohibited (default): GPL / AGPL

### R7) Testing Conventions
- Test naming: `UserServiceTest`, method names can use backtick style
- Use JUnit 5 (`@Test`, `@Nested`, `@DisplayName`)
- Assertions: `assertEquals`, `assertTrue`, `assertNotNull` — never `assert()`
- Mock with Mockito or MockK (for Kotlin)
- Integration tests with `@SpringBootTest`

### R8) Build & Verification
- Full verify: `./gradlew clean build` or `./mvnw clean verify`
- Unit tests: `./gradlew test` or `./mvnw test`
- Lint/Format: check with `./gradlew tasks` first, use if available

## EXAMPLES
- BAD: Adding "might use later" interfaces/generics
- GOOD: Minimal structure satisfying current requirements + tests
- BAD: `System.out.println("debug: " + password)`
- GOOD: `log.debug("User login attempt for userId={}", userId)`
