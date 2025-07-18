# Session Management Fix Plan

## Issue Summary
The search command (`uv run ca-bhfuil search --repo nova sean`) was failing with `IllegalStateChangeError` due to improper async context manager usage in database session management.

## Root Cause Analysis
**Error**: `IllegalStateChangeError: Method 'close()' can't be called here; method '_connection_for_bind()' is already in progress`

**Location**: `/Users/sean/repos/ca-bhfuil/src/ca_bhfuil/core/managers/base.py`

**Problem**:
- Lines 52 & 167: Manual `__aenter__()` calls on async context managers
- No corresponding `__aexit__()` calls for proper cleanup
- Sessions never properly closed via context manager protocol
- Resource leaks causing SQLAlchemy connection warnings

## Fix Applied
### Changes Made to BaseManager Class

1. **Added Context Manager Tracking**:
   - Added `_session_context_manager` field to track active async context managers
   - Type: `typing.AsyncContextManager[sqlalchemy.ext.asyncio.AsyncSession] | None`

2. **Fixed `_get_db_repository()` Method**:
   - Store reference to context manager before calling `__aenter__()`
   - Proper cleanup via `__aexit__()` in close method

3. **Fixed `_get_session_for_transaction()` Method**:
   - Store reference to context manager before calling `__aenter__()`
   - Consistent with `_get_db_repository()` pattern

4. **Updated `close()` Method**:
   - Call `__aexit__(None, None, None)` on stored context manager
   - Proper exception handling for cleanup errors
   - Reset all session-related fields to None

### Code Changes
```python
# Before (BROKEN):
self._db_session = await db_manager.engine.get_session().__aenter__()

# After (FIXED):
self._session_context_manager = db_manager.engine.get_session()
self._db_session = await self._session_context_manager.__aenter__()

# Cleanup in close():
if self._session_owned and self._session_context_manager:
    try:
        await self._session_context_manager.__aexit__(None, None, None)
    except Exception as e:
        logger.debug(f"Error closing session context manager: {e}")
    finally:
        self._session_context_manager = None
        self._db_session = None
        self._db_repository = None
```

## Testing Plan
### Primary Test
Run the failing command to verify fix:
```bash
uv run ca-bhfuil search --repo nova sean
```

**Expected Results**:
- No `IllegalStateChangeError` exceptions
- No SQLAlchemy connection warnings
- Search completes successfully (may return 0 results, that's OK)
- Clean shutdown without resource leaks

### Secondary Tests
1. **Unit Tests**: Run existing test suite
   ```bash
   uv run pytest tests/unit/test_base_manager.py -v
   ```

2. **Integration Tests**: Run manager integration tests
   ```bash
   uv run pytest tests/integration/ -v
   ```

3. **Full Test Suite**: Ensure no regressions
   ```bash
   uv run pytest
   ```

## Verification Checklist
- [ ] Command runs without `IllegalStateChangeError`
- [ ] No SQLAlchemy connection warnings in output
- [ ] Database sessions properly closed (no resource leaks)
- [ ] All existing tests pass
- [ ] Memory usage stable (no session accumulation)

## Alternative Approaches Considered
1. **Full Async Context Manager Pattern**: Rewrite to use `async with` statements
   - **Pros**: More Pythonic, cleaner code
   - **Cons**: Major refactor, affects all manager usage patterns
   - **Decision**: Deferred for future architectural improvement

2. **Session Pooling**: Implement session reuse
   - **Pros**: Better performance
   - **Cons**: More complexity, potential for session state issues
   - **Decision**: Not needed for current fix

## Future Improvements
1. **Refactor to Async Context Manager Pattern**:
   - Convert BaseManager to proper async context manager
   - Use `async with` throughout codebase
   - Cleaner resource management

2. **Add Session State Validation**:
   - Validate session state before operations
   - Better error messages for session issues
   - Prevent double-closing scenarios

3. **Performance Monitoring**:
   - Track session creation/destruction
   - Monitor for session leaks
   - Performance metrics for database operations

## Rollback Plan
If the fix causes issues:
1. Revert `/Users/sean/repos/ca-bhfuil/src/ca_bhfuil/core/managers/base.py` to previous version
2. The issue will return but system will be stable
3. Consider alternative approaches from list above

## Files Modified
- `/Users/sean/repos/ca-bhfuil/src/ca_bhfuil/core/managers/base.py` - Session management fix

## Next Steps
1. Test the fix on a stable system
2. Run full test suite to ensure no regressions
3. Monitor for any new session-related issues
4. Consider architectural improvements for future releases

---

**Status**: Fix applied, ready for testing
**Priority**: High - Core functionality affected
**Testing Environment**: Work computer (Mac system has Claude Code stability issues)
