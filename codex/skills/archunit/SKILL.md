---
name: archunit
description: Enforce architecture rules as automated tests with ArchUnit. Validate layered boundaries (Controller → Service → Repository), package dependency constraints, cycle freedom, annotation consistency, and hexagonal isolation in Java and Kotlin Spring Boot projects.
---

# ArchUnit — Architecture Rules as Tests

ArchUnit turns architecture guidelines into executable JUnit tests. Instead of relying on code review to catch violations, you encode the rule once and let CI block the violation.

## When to Use

- Forbid a specific package-to-package dependency and have CI enforce it.
- Recurring review comments need to become tests.
- Migrating a legacy module and need to prove no direct calls to old code.
- Guarantee naming or annotation conventions.
- Introduce a hexagonal boundary and prove domain has zero framework imports.

## Setup

```kotlin
// Gradle Kotlin DSL
dependencies {
    testImplementation("com.tngtech.archunit:archunit-junit5:1.3.0")
}
```

## Core Rule Templates

### Layered Architecture
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

### Hexagonal Isolation
```java
@ArchTest
static final ArchRule domain_has_no_framework_imports =
    noClasses().that().resideInAPackage("..domain..")
        .should().dependOnClassesThat().resideInAnyPackage(
            "org.springframework..", "jakarta.persistence..", "org.hibernate..")
        .because("the domain model must stay framework-agnostic");
```

### Cycle Freedom
```java
@ArchTest
static final ArchRule no_package_cycles =
    SlicesRuleDefinition.slices()
        .matching("com.example.(*)..")
        .should().beFreeOfCycles();
```

### Naming Conventions
```java
@ArchTest
static final ArchRule services_end_with_service =
    classes().that().resideInAPackage("..service..")
        .and().areNotInterfaces()
        .should().haveSimpleNameEndingWith("Service");
```

## Kotlin Adaptation

- Declarative `@ArchTest` fields: `companion object` + `@JvmField val`
- Use `::class.java` for `Class<?>` references
- Backtick-named test methods for imperative/SoftAssertion style

## Gradual Adoption

- **`allowEmptyShould(true)`**: pre-arm rules that currently select nothing.
- **`FreezingArchRule`**: snapshot existing violations, fail only on new ones. Commit the store.
- Roll out in waves: layering → cycles → domain isolation → naming → annotations.

## Checklist

- [ ] `archunit-junit5` 1.3.x as test-scope dependency
- [ ] Every rule ends with `.because("…")`
- [ ] Custom checks use `SoftAssertions` for full violation list
- [ ] `consideringAllDependencies()` on layered rules
- [ ] Each rule verified against intentional violation during development
- [ ] Architecture tests run in default CI `test`/`check` task
