---
name: archunit
description: Enforce architecture rules as automated tests with ArchUnit. Validate layered boundaries (Controller → Service → Repository), package dependency constraints, cycle freedom, annotation consistency, and hexagonal isolation in Java and Kotlin Spring Boot projects. Use when introducing architecture tests, preventing recurring review violations, or migrating legacy modules with dependency constraints.
---

# ArchUnit — Architecture Rules as Tests

ArchUnit turns architecture guidelines into executable JUnit tests. Instead of relying on code review to catch a Controller that reaches into a Repository or a domain class that imports Spring, you encode the rule once and let CI block the violation.

This skill focuses on **writing and enforcing** rules. For the underlying design ideas see `skills/hexagonal-architecture/SKILL.md` (ports & adapters) and `skills/springboot-patterns/SKILL.md` (layered Spring Boot implementation). ArchUnit is how you keep those designs from eroding.

## When to Use

- You want to forbid a specific package-to-package dependency (e.g. `..support..` must not reach business packages) and have CI enforce it.
- Recurring review comments — "don't call the repository from the controller", "don't put `@Transactional` outside the service layer" — need to become tests.
- You are migrating a legacy module (e.g. replacing an engine without downtime) and need to prove that the new module never calls the old one directly.
- Your team agreed on naming or annotation conventions (Swagger `@ApiModel`, `@NotNull` + `@Nonnull` co-occurrence) and wants to guarantee them.
- You are introducing a hexagonal boundary and need to prove the domain has zero framework imports.

## Setup

### Maven

```xml
<dependency>
    <groupId>com.tngtech.archunit</groupId>
    <artifactId>archunit-junit5</artifactId>
    <version>1.3.0</version>
    <scope>test</scope>
</dependency>
```

### Gradle (Kotlin DSL)

```kotlin
dependencies {
    testImplementation("com.tngtech.archunit:archunit-junit5:1.3.0")
}
```

### Test skeleton

```java
@AnalyzeClasses(
    packages = "com.example",
    importOptions = ImportOption.DoNotIncludeTests.class
)
class ArchitectureTest {

    @ArchTest
    static final ArchRule example_rule = /* ... */;
}
```

`@AnalyzeClasses` imports once per JVM and caches; every `@ArchTest` field or method is a separate rule. Prefer `DoNotIncludeTests` so test utilities don't pollute your dependency graph.

## Three Checking Styles

ArchUnit supports three distinct ways to assert rules. They are not exclusive — most projects combine them.

| Style | Best for | Failure mode |
|---|---|---|
| **Declarative** (`rule.check(classes)` or `@ArchTest`) | Structural rules (layers, packages, dependencies, cycles) | Stops at first violation class, prints full list |
| **Imperative** (loop + `assertThat`) | Custom per-class/per-method assertions that need context the DSL lacks | Stops at first violation — hard to see the big picture |
| **AssertJ + SoftAssertion** | Same as imperative but you want the full list of violations in one run, with custom source-location messages | Collects everything, reports at the end |

### Declarative

```java
@ArchTest
static final ArchRule support_must_not_reach_charge =
    noClasses().that().resideInAPackage("..support..")
        .should().accessClassesThat().resideInAPackage("..charge..")
        .because("support is a shared utility layer and must stay leaf-level");
```

### Imperative

```java
@Test
void api_operation_id_must_not_contain_whitespace() {
    JavaClasses classes = new ClassFileImporter().importPackages("com.example");
    for (JavaClass clazz : classes) {
        if (!clazz.isAnnotatedWith(ApiOperationId.class)) continue;
        String id = clazz.getAnnotationOfType(ApiOperationId.class).value();
        assertThat(id).doesNotContain(" ");
    }
}
```

The imperative style is powerful but halts at the first failing class. You learn about one violation per run.

### AssertJ SoftAssertion integration (recommended for custom checks)

```java
@Test
void api_operation_id_must_not_contain_whitespace() {
    SoftAssertions softly = new SoftAssertions();
    JavaClasses classes = new ClassFileImporter().importPackages("com.example");

    for (JavaClass clazz : classes) {
        if (clazz.isAnnotatedWith(ApiOperationId.class)) {
            String id = clazz.getAnnotationOfType(ApiOperationId.class).value();
            softly.assertThat(id)
                .describedAs("@ApiOperationId must not contain spaces at %s",
                    clazz.getSource().map(Object::toString).orElse(clazz.getName()))
                .doesNotContain(" ");
        }
    }
    softly.assertAll();
}
```

`SoftAssertion` lets every violation surface in a single run and `describedAs` prints the class location. This is the Naver team's preferred style for custom rules and it pairs well with `@ArchTest` declarative rules.

## Case Studies

The four cases below are reconstructed from the Naver D2 article ["ArchUnit을 사용한 아키텍처 검증"](https://d2.naver.com/helloworld/9222129). Domain names are kept close to the original for continuity; adapt the package literals to your project.

### Case 1 — Support package must not depend on business packages

**Problem.** A shared `..support..` package holds annotations, API clients, and criteria objects. Anyone may use `support`, but `support` itself must stay leaf-level. Developers kept adding back-references from support into the `charge` business module, which created cycles and made support impossible to extract.

**Rule.** Declarative is enough because this is a pure package-to-package assertion.

**Java**

```java
@ArchTest
static final ArchRule support_must_not_depend_on_charge =
    noClasses().that().resideInAPackage("..support..")
        .should().accessClassesThat().resideInAPackage("..charge..")
        .because("support is a shared leaf module; back-references create cycles");
```

**Kotlin**

```kotlin
@AnalyzeClasses(packages = ["com.example"])
class ArchitectureTest {
    companion object {
        @ArchTest
        @JvmField
        val supportMustNotDependOnCharge: ArchRule =
            noClasses().that().resideInAPackage("..support..")
                .should().accessClassesThat().resideInAPackage("..charge..")
                .because("support is a shared leaf module; back-references create cycles")
    }
}
```

Kotlin note: declarative rules need to be `@JvmField val` (or `@JvmStatic fun`) inside a `companion object` so the JUnit engine can discover them as static members.

### Case 2 — Swagger `@ApiModel` value must match the class name

**Problem.** The team generates API docs from `@ApiModel` but the `value` attribute drifted out of sync with class names during refactors. Documentation silently pointed to the wrong schemas.

**Rule.** Needs per-class context (class name → annotation value) and should report *all* mismatches in one run. Use imperative iteration + SoftAssertion.

**Java**

```java
@Test
void api_model_value_must_equal_class_name() {
    SoftAssertions softly = new SoftAssertions();
    JavaClasses classes = new ClassFileImporter()
        .importPackages("com.example.charge.param");

    for (JavaClass clazz : classes) {
        Optional<JavaAnnotation<JavaClass>> annotation = clazz.tryGetAnnotationOfType("io.swagger.annotations.ApiModel");
        if (annotation.isEmpty()) continue;

        String declared = (String) annotation.get().get("value").orElse("");
        String expected = clazz.getSimpleName();

        softly.assertThat(declared)
            .describedAs("%s must be annotated with @ApiModel(\"%s\") at %s",
                expected, expected, clazz.getSource().map(Object::toString).orElse(clazz.getName()))
            .isEqualTo(expected);
    }
    softly.assertAll();
}
```

**Kotlin**

```kotlin
@Test
fun `ApiModel value must equal class name`() {
    val softly = SoftAssertions()
    val classes = ClassFileImporter().importPackages("com.example.charge.param")

    for (clazz in classes) {
        val annotation = clazz.tryGetAnnotationOfType("io.swagger.annotations.ApiModel")
        if (annotation.isEmpty) continue

        val declared = annotation.get().get("value").orElse("") as String
        val expected = clazz.simpleName

        softly.assertThat(declared)
            .describedAs("$expected must be annotated with @ApiModel(\"$expected\") at ${clazz.source.map(Any::toString).orElse(clazz.name)}")
            .isEqualTo(expected)
    }
    softly.assertAll()
}
```

### Case 3 — Fields must carry both `@NotNull` and `@Nonnull` (except `@Id`/`@LazyInit`)

**Problem.** The team uses two orthogonal null checks: `jakarta.validation.constraints.NotNull` for request/persistence validation and `javax.annotation.Nonnull` for IDE/static analysis. A field that had one but not the other produced partial protection.

**Rule.** A field predicate picks the relevant fields, then the DSL demands both annotations.

**Java**

```java
@ArchTest
static final ArchRule nullability_annotations_must_agree =
    fields().that(new DescribedPredicate<JavaField>(
            "are non-Id, non-LazyInit fields already carrying @Nonnull or @NotNull") {
        @Override
        public boolean test(JavaField field) {
            boolean skipped = field.isAnnotatedWith(Id.class) || field.isAnnotatedWith(LazyInit.class);
            boolean partiallyAnnotated = field.isAnnotatedWith(Nonnull.class)
                || field.isAnnotatedWith(NotNull.class);
            return !skipped && partiallyAnnotated;
        }
    })
    .should().beAnnotatedWith(NotNull.class)
    .andShould().beAnnotatedWith(Nonnull.class)
    .because("both annotations must agree so runtime validation and static analysis stay in sync");
```

**Kotlin**

```kotlin
@ArchTest
@JvmField
val nullabilityAnnotationsMustAgree: ArchRule =
    fields().that(object : DescribedPredicate<JavaField>(
        "are non-Id, non-LazyInit fields already carrying @Nonnull or @NotNull") {
        override fun test(field: JavaField): Boolean {
            val skipped = field.isAnnotatedWith(Id::class.java) || field.isAnnotatedWith(LazyInit::class.java)
            val partial = field.isAnnotatedWith(Nonnull::class.java)
                || field.isAnnotatedWith(NotNull::class.java)
            return !skipped && partial
        }
    })
        .should().beAnnotatedWith(NotNull::class.java)
        .andShould().beAnnotatedWith(Nonnull::class.java)
        .because("runtime validation and static analysis must agree")
```

### Case 4 — Legacy engine replacement: `benefit` must not call `benefit_core` directly

**Problem.** During a zero-downtime engine replacement the team introduced an `adapter` layer and needed to prove that no code path in `benefit` still reaches `benefit_core` directly. Reviewing by hand was infeasible.

**Rule.** `withImportOption` narrows the import scope to only the legacy directory, then a plain declarative rule proves the constraint. For finer grained diagnostics (which caller? which field?) use imperative SoftAssertion on top.

**Java**

```java
private static final JavaClasses legacyCore = new ClassFileImporter()
    .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
    .withImportOption(location -> location.contains("/benefit_core/"))
    .importPackages("com.example.benefit");

@ArchTest
static final ArchRule benefit_must_go_through_adapter =
    noClasses().that().resideInAPackage("..benefit..")
        .and().resideOutsideOfPackage("..benefit.adapter..")
        .should().dependOnClassesThat().resideInAPackage("..benefit_core..")
        .because("legacy engine is reachable only through the adapter during migration");
```

**Kotlin**

```kotlin
companion object {
    private val legacyCore: JavaClasses = ClassFileImporter()
        .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
        .withImportOption { it.contains("/benefit_core/") }
        .importPackages("com.example.benefit")

    @ArchTest
    @JvmField
    val benefitMustGoThroughAdapter: ArchRule =
        noClasses().that().resideInAPackage("..benefit..")
            .and().resideOutsideOfPackage("..benefit.adapter..")
            .should().dependOnClassesThat().resideInAPackage("..benefit_core..")
            .because("legacy engine is reachable only through the adapter during migration")
}
```

For the "list every caller" output the team reported, wrap the check in a SoftAssertion loop that walks every `JavaField` and `JavaMethodCall` on the caller side and records `AnalyzedCaller` entries before `assertAll()`.

## Core Rule Templates

General-purpose templates that almost every Spring Boot project can adopt. Compose them with the case-study patterns above.

### Layered architecture (Controller → Service → Repository)

```java
@ArchTest
static final ArchRule layered_architecture =
    layeredArchitecture()
        .consideringAllDependencies()
        .layer("Controller").definedBy("..controller..")
        .layer("Service").definedBy("..service..")
        .layer("Repository").definedBy("..repository..")
        .whereLayer("Controller").mayNotBeAccessedByAnyLayer()
        .whereLayer("Service").mayOnlyBeAccessedByLayers("Controller")
        .whereLayer("Repository").mayOnlyBeAccessedByLayers("Service");
```

Since ArchUnit 1.x, `layeredArchitecture()` requires an explicit mode — `consideringAllDependencies()` is the sensible default.

### Hexagonal isolation (`domain` must not depend on frameworks)

```java
@ArchTest
static final ArchRule domain_has_no_framework_imports =
    noClasses().that().resideInAPackage("..domain..")
        .should().dependOnClassesThat().resideInAnyPackage(
            "org.springframework..",
            "jakarta.persistence..",
            "org.hibernate.."
        )
        .because("the domain model must stay framework-agnostic — see skills/hexagonal-architecture");
```

Pair this with `application` → only port interfaces, and `adapter.*` → implements the port interfaces, to close the hexagon.

### Cycle freedom across slices

```java
@ArchTest
static final ArchRule no_package_cycles =
    SlicesRuleDefinition.slices()
        .matching("com.example.(*)..")
        .should().beFreeOfCycles();
```

Use one slicing dimension per test — `com.example.(*)..` (top-level modules), then optionally a second test for `com.example.*.(*)..` (submodules).

### Naming conventions

```java
@ArchTest
static final ArchRule services_end_with_service =
    classes().that().resideInAPackage("..service..")
        .and().areNotInterfaces()
        .and().areNotInnerClasses()
        .should().haveSimpleNameEndingWith("Service");
```

### Annotation placement (`@Transactional` on service layer only)

```java
@ArchTest
static final ArchRule transactional_only_on_service =
    methods().that().areAnnotatedWith(Transactional.class)
        .should().beDeclaredInClassesThat().resideInAPackage("..service..")
        .because("transaction boundaries belong to the service layer");
```

## Kotlin Adaptation

Kotlin needs a few mechanical tweaks to cooperate with JUnit 5 and ArchUnit's discovery.

- Declarative `@ArchTest` fields must be in a `companion object` as `@JvmField val` or exposed via `@JvmStatic fun`. A plain Kotlin property is invisible to the engine.
- Use `::class.java` wherever the Java API expects `Class<?>`.
- Class references in package literals are the same as Java — ArchUnit reads bytecode, not source.
- Backtick-named test methods work for the imperative/SoftAssertion style.

```kotlin
@AnalyzeClasses(
    packages = ["com.example"],
    importOptions = [ImportOption.DoNotIncludeTests::class]
)
class ArchitectureTest {
    companion object {
        @ArchTest
        @JvmField
        val layered: ArchRule =
            layeredArchitecture()
                .consideringAllDependencies()
                .layer("Controller").definedBy("..controller..")
                .layer("Service").definedBy("..service..")
                .layer("Repository").definedBy("..repository..")
                .whereLayer("Controller").mayNotBeAccessedByAnyLayer()
                .whereLayer("Service").mayOnlyBeAccessedByLayers("Controller")
                .whereLayer("Repository").mayOnlyBeAccessedByLayers("Service")
    }
}
```

See `rules/11-stack-kotlin.md` for Kotlin interop conventions that overlap with ArchUnit rules (e.g. constructor injection, sealed classes).

## Gradual Adoption Strategy

Introducing ArchUnit into a mature codebase rarely finds zero violations. Two mechanisms let you merge a rule without stopping the world:

1. **`allowEmptyShould(true)`** — for rules that currently select nothing but you want to pre-arm.

   ```java
   @ArchTest
   static final ArchRule future_rule =
       noClasses().that().resideInAPackage("..legacy..")
           .should().accessClassesThat().resideInAPackage("..new_api..")
           .allowEmptyShould(true);
   ```

2. **`FreezingArchRule` + `ViolationStore`** — snapshot existing violations, fail only on *new* ones.

   ```java
   @ArchTest
   static final ArchRule frozen_layering =
       FreezingArchRule.freeze(
           noClasses().that().resideInAPackage("..controller..")
               .should().dependOnClassesThat().resideInAPackage("..repository..")
       );
   ```

   Configure the store in `src/test/resources/archunit.properties`:

   ```properties
   freeze.store.default.path=archunit_store
   freeze.refreeze=false
   ```

   Commit the store directory. Reviewers can read it like a violation budget: the set should only shrink over time.

Roll out rules in waves: layering → cycles → domain isolation → naming → annotation placement. One wave per PR so blame is easy.

## CI/CD Integration

- **Gradle**: `./gradlew test --tests "*ArchitectureTest"` — add it to the default `check` task; no new lifecycle needed.
- **Maven**: `mvn -Dtest='*ArchitectureTest' test` — or leave it to the regular `test` phase.
- **Reports**: ArchUnit emits JUnit XML through the runner, so Jenkins, GitHub Actions `dorny/test-reporter`, and GitLab test summaries all render violations inline.
- **Fail fast locally**: wire it into a pre-push Git hook only if the full suite is fast. Most projects keep it in CI to avoid punishing local experimentation.
- **Reviewer signal**: when a rule fails, the error message includes `because("…")` text — invest in good reasons because they are the feedback the reviewer actually reads.

## Anti-Patterns

- **Over-regex'd package literals.** `..impl.v2.internal.detail.*..` is brittle and unreadable. Prefer slicing plus `resideInAPackage` with a single level of wildcards and rely on naming to do the rest.
- **Freezing cycles indefinitely.** A cycle is a correctness risk, not a style opinion. Freeze once, open a follow-up issue, and remove the entry in the same sprint. Do not let `freeze.refreeze=true` become the norm.
- **Rules without `because(...)`.** "Rule 'noClasses...' was violated" tells the next developer nothing. Always encode the motivation; it is the difference between an obstacle and a guardrail.
- **Big-bang rule adoption.** Dropping ten rules on a team at once generates a backlog nobody owns. Land them one at a time, paired with fixes, so each rule proves its worth before the next arrives.
- **Rules that were never tried red.** If you never saw a rule fail on an intentional violation during development, you do not know whether it matches the packages you expect. Run it against a deliberately-broken branch before merging.

## Checklist

- [ ] `archunit-junit5` 1.3.x is a test-scope dependency.
- [ ] `@AnalyzeClasses` narrows imports and excludes tests.
- [ ] Every declarative rule ends with `.because("…")` explaining the intent.
- [ ] Custom checks use `SoftAssertions` so a single run lists every violation.
- [ ] Layered-architecture rule calls `consideringAllDependencies()` or an explicit alternative.
- [ ] Domain isolation rule lists framework packages your team actually forbids.
- [ ] Cycle-free rule covers at least one meaningful slicing dimension.
- [ ] Legacy violations are captured via `FreezingArchRule` + committed store, not comments.
- [ ] Each rule was verified against an intentional violation during development.
- [ ] Architecture tests run as part of the default CI `test`/`check` task.
- [ ] Kotlin rules are declared as `@JvmField val` or `@JvmStatic fun` inside a `companion object`.

## Related Skills & Rules

- `skills/hexagonal-architecture/SKILL.md` — the design that the domain-isolation rule enforces.
- `skills/springboot-patterns/SKILL.md` — the implementation that the layered rule keeps honest.
- `skills/kotlin-patterns/SKILL.md` — idiomatic Kotlin constructs referenced in the Kotlin examples.
- `rules/10-stack-java-spring.md` — Java/Spring conventions (constructor injection, `@Transactional`, logging) that map cleanly onto ArchUnit rules.
- `rules/11-stack-kotlin.md` — Kotlin conventions (null safety, sealed classes) that pair with the nullability annotation case.

## Resources

- ArchUnit project — https://www.archunit.org/
- ArchUnit source and examples — https://github.com/TNG/ArchUnit
- User guide (API reference, layered architecture, freezing) — https://www.archunit.org/userguide/html/000_Index.html
- Naver D2 case study (original inspiration for the four cases above) — https://d2.naver.com/helloworld/9222129
