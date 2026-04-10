---
name: kotlin-patterns
description: Idiomatic Kotlin patterns, best practices, and conventions for building robust, efficient, and maintainable Kotlin applications with coroutines, null safety, and DSL builders.
---

# Kotlin Development Patterns

Idiomatic Kotlin patterns and best practices.

## When to Use

- Writing, reviewing, or refactoring Kotlin code
- Designing Kotlin modules or libraries
- Configuring Gradle Kotlin DSL builds

## Core Principles

### 1. Null Safety
```kotlin
// Good: Safe calls and Elvis operator
fun getUserEmail(userId: String): String {
    val user = userRepository.findById(userId)
    return user?.email ?: "unknown@example.com"
}

// Bad: Force-unwrapping
val name = user!!.name  // Throws NPE if null
```

### 2. Immutability by Default
```kotlin
data class User(val id: String, val name: String, val email: String)

// Transform with copy()
fun updateEmail(user: User, newEmail: String): User = user.copy(email = newEmail)
```

### 3. Sealed Classes for Exhaustive Hierarchies
```kotlin
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Failure(val error: AppError) : Result<Nothing>()
    data object Loading : Result<Nothing>()
}
```

### 4. Scope Functions
```kotlin
// let: Transform nullable
val length: Int? = name?.let { it.trim().length }

// apply: Configure object
val user = User().apply { name = "Alice"; email = "alice@example.com" }

// also: Side effects
val user = createUser(request).also { logger.info("Created: ${it.id}") }
```

### 5. Coroutines — Structured Concurrency
```kotlin
suspend fun fetchUserWithPosts(userId: String): UserProfile =
    coroutineScope {
        val user = async { userService.getUser(userId) }
        val posts = async { postService.getUserPosts(userId) }
        UserProfile(user = user.await(), posts = posts.await())
    }
```

### 6. Flow for Reactive Streams
```kotlin
fun searchUsers(query: Flow<String>): Flow<List<User>> =
    query
        .debounce(300.milliseconds)
        .distinctUntilChanged()
        .filter { it.length >= 2 }
        .mapLatest { q -> userRepository.search(q) }
        .catch { emit(emptyList()) }
```

### 7. Extension Functions
```kotlin
fun String.toSlug(): String =
    lowercase().replace(Regex("[^a-z0-9\\s-]"), "").replace(Regex("\\s+"), "-").trim('-')
```

## Anti-Patterns to Avoid

- `!!` (force-unwrap) — use `?.`, `?:`, or `requireNotNull`
- Mutable data classes — prefer `val` + `copy()`
- `GlobalScope.launch` — use structured concurrency
- Deeply nested scope functions — chain safe calls instead
- Exceptions for control flow — use nullable return or `Result`

## Quick Reference

| Idiom | Description |
|-------|-------------|
| `val` over `var` | Prefer immutable variables |
| `data class` | For value objects with equals/hashCode/copy |
| `sealed class/interface` | For restricted type hierarchies |
| `value class` | For type-safe wrappers with zero overhead |
| `require`/`check` | Precondition assertions |
| `Flow` | Cold reactive streams |
| Delegation `by` | Reuse implementation without inheritance |
