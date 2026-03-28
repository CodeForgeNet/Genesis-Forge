---
description: Test generation and execution. Creates and runs tests for code.
---

# /test — $ARGUMENTS

## Sub-commands
```
/test                - Run all tests
/test [file/feature] - Generate tests for target
/test coverage       - Show coverage report
/test watch          - Watch mode
```

## Behavior: Generate Tests
1. Analyze code — identify functions, edge cases, dependencies to mock
2. Generate: happy path + error cases + edge cases
3. Use project's framework (Jest/Vitest), follow existing patterns

## Output Format

**Generation:**
```
## 🧪 Tests: [Target]
### Test Plan
| Test Case | Type | Coverage |

### Generated Tests
`tests/[file].test.ts`
[code]
Run with: `npm test`
```

**Execution:**
```
🧪 Running tests...
✅ auth.test.ts (5 passed)
❌ order.test.ts (1 failed)
Total: 15 tests (14 passed, 1 failed)
```

## Principles
- Test behavior, not implementation
- Arrange-Act-Assert pattern
- Mock external dependencies
- One assertion per test (when practical)
