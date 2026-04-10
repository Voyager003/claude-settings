---
name: springboot-patterns
description: Spring Boot architecture patterns, REST API design, layered services, data access, caching, async processing, and logging. Targets Spring Boot 4.0+ (Spring Framework 7.x baseline). Use for Java Spring Boot backend work.
---

# Spring Boot Development Patterns

Spring Boot architecture and API patterns for scalable, production-grade services. Targets **Spring Boot 4.0+**.

## When to Activate

- Building REST APIs with Spring MVC or WebFlux
- Structuring controller → service → repository layers
- Configuring Spring Data JPA, caching, or async processing
- Adding validation, exception handling, or pagination

## REST API Structure

```java
@RestController
@RequestMapping("/api/markets")
@Validated
class MarketController {
  private final MarketService marketService;

  MarketController(MarketService marketService) {
    this.marketService = marketService;
  }

  @GetMapping
  ResponseEntity<Page<MarketResponse>> list(
      @RequestParam(defaultValue = "0") int page,
      @RequestParam(defaultValue = "20") int size) {
    return ResponseEntity.ok(marketService.list(PageRequest.of(page, size)).map(MarketResponse::from));
  }

  @PostMapping
  ResponseEntity<MarketResponse> create(@Valid @RequestBody CreateMarketRequest request) {
    Market market = marketService.create(request);
    return ResponseEntity.status(HttpStatus.CREATED).body(MarketResponse.from(market));
  }
}
```

## DTOs and Validation

```java
public record CreateMarketRequest(
    @NotBlank @Size(max = 200) String name,
    @NotBlank @Size(max = 2000) String description,
    @NotNull @FutureOrPresent Instant endDate) {}
```

## Exception Handling

```java
@ControllerAdvice
class GlobalExceptionHandler {
  @ExceptionHandler(MethodArgumentNotValidException.class)
  ResponseEntity<ApiError> handleValidation(MethodArgumentNotValidException ex) {
    String message = ex.getBindingResult().getFieldErrors().stream()
        .map(e -> e.getField() + ": " + e.getDefaultMessage())
        .collect(Collectors.joining(", "));
    return ResponseEntity.badRequest().body(ApiError.validation(message));
  }
}
```

## Key Patterns

- **Repository**: `JpaRepository` with custom `@Query` for complex queries
- **Service**: `@Transactional` for writes, `@Transactional(readOnly = true)` for reads
- **Caching**: `@Cacheable`, `@CacheEvict` with `@EnableCaching`
- **Async**: `@Async` + `CompletableFuture` with `@EnableAsync`
- **Logging**: SLF4J (`LoggerFactory`), never `System.out`, never log secrets
- **Filters**: `OncePerRequestFilter` for request logging, rate limiting

## Production Defaults

- Prefer constructor injection, avoid field injection
- Enable `spring.mvc.problemdetails.enabled=true` for RFC 7807 errors
- Configure HikariCP pool sizes for workload, set timeouts
- Use records for DTOs with Bean Validation annotations
