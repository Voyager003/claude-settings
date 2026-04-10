---
name: hexagonal-architecture
description: Design, implement, and refactor Ports & Adapters systems with clear domain boundaries, dependency inversion, and testable use-case orchestration across TypeScript, Java, Kotlin, and Go services.
---

# Hexagonal Architecture

Hexagonal architecture (Ports and Adapters) keeps business logic independent from frameworks, transport, and persistence details.

## When to Use

- Building new features where long-term maintainability and testability matter.
- Refactoring layered or framework-heavy code where domain logic is mixed with I/O concerns.
- Supporting multiple interfaces for the same use case (HTTP, CLI, queue workers, cron jobs).
- Replacing infrastructure (database, external APIs, message bus) without rewriting business rules.

## Core Concepts

- **Domain model**: Business rules and entities/value objects. No framework imports.
- **Use cases (application layer)**: Orchestrate domain behavior and workflow steps.
- **Inbound ports**: Contracts describing what the application can do.
- **Outbound ports**: Contracts for dependencies the application needs (repositories, gateways, etc.).
- **Adapters**: Infrastructure and delivery implementations of ports.
- **Composition root**: Single wiring location where concrete adapters are bound to use cases.

Dependency direction is always inward:
- Adapters -> application/domain
- Application -> port interfaces
- Domain -> nothing external

## Suggested Module Layout

```text
src/
  features/
    orders/
      domain/
        Order.ts
        OrderPolicy.ts
      application/
        ports/
          inbound/
            CreateOrder.ts
          outbound/
            OrderRepositoryPort.ts
            PaymentGatewayPort.ts
        use-cases/
          CreateOrderUseCase.ts
      adapters/
        inbound/
          http/
            createOrderRoute.ts
        outbound/
          postgres/
            PostgresOrderRepository.ts
      composition/
        ordersContainer.ts
```

## Multi-Language Mapping

- **TypeScript**: Ports as interfaces/types in `application/ports/*`. Composition via explicit factory/container.
- **Java**: Packages: `domain`, `application.port.in`, `application.port.out`, `adapter.in`, `adapter.out`. Spring config or manual wiring.
- **Kotlin**: Mirror Java split. Koin/Dagger/Spring/manual DI.
- **Go**: Packages: `internal/<feature>/domain`, `application`, `ports`, `adapters/*`. Small interfaces owned by consuming package.

## Anti-Patterns to Avoid

- Domain entities importing ORM models, web framework types, or SDK clients.
- Use cases reading directly from `req`, `res`, or queue metadata.
- Returning database rows directly from use cases without domain mapping.
- Letting adapters call each other directly instead of flowing through ports.
- Spreading dependency wiring across many files with hidden global singletons.

## Migration Playbook

1. Pick one vertical slice with frequent change pain.
2. Extract a use-case boundary with explicit input/output types.
3. Introduce outbound ports around existing infrastructure calls.
4. Move orchestration logic from controllers/services into the use case.
5. Add tests around the new boundary (unit + adapter integration).
6. Repeat slice-by-slice; avoid full rewrites.

## Testing Guidance

- **Domain tests**: pure business rules (no mocks, no framework setup).
- **Use-case unit tests**: fakes/stubs for outbound ports.
- **Outbound adapter contract tests**: shared contract suites run against each adapter.
- **Inbound adapter tests**: verify protocol mapping.
- **E2E tests**: critical user journeys through the full stack.
