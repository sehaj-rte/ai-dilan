# Progress Tracking - Infinite Loop Fix

## Issue

The initial implementation had an infinite loop issue where the frontend was continuously fetching the experts list and progress updates, causing excessive API calls.

## Root Cause

The `useEffect` hook had a dependency on the entire `experts` array, which caused it to re-run every time the experts state changed, creating an infinite loop:

```typescript
// ❌ WRONG - Causes infinite loop
useEffect(() => {
  fetchExperts()
  const progressInterval = setInterval(() => {
    fetchProgressForExperts()
  }, 2000)
  return () => clearInterval(progressInterval)
}, [experts]) // This dependency causes the loop!
```

## Solution

### 1. Separate useEffect Hooks

Split the initial fetch and polling into separate `useEffect` hooks:

```typescript
// ✅ CORRECT - Initial fetch only once
useEffect(() => {
  fetchExperts()
}, [])

// ✅ CORRECT - Polling only depends on experts.length
useEffect(() => {
  if (experts.length === 0) return
  
  fetchProgressForExperts() // Initial fetch
  
  const progressInterval = setInterval(() => {
    fetchProgressForExperts()
  }, 2000)
  
  return () => clearInterval(progressInterval)
}, [experts.length]) // Only re-run if number of experts changes
```

### 2. Optimize Progress Updates

Only update state when there are active (non-completed) progress records:

```typescript
// Only update if status is not completed
if (result.progress.status !== 'completed') {
  progressMap[result.expertId] = result.progress
}

// Only update state if there are active progress records
if (Object.keys(progressMap).length > 0) {
  setExpertProgress(progressMap)
} else {
  setExpertProgress({}) // Clear when all completed
}
```

## Benefits

✅ **No Infinite Loop** - Hooks only run when necessary
✅ **Reduced API Calls** - Only polls for progress, not entire experts list
✅ **Better Performance** - State updates only when needed
✅ **Cleaner Code** - Separation of concerns

## API Call Pattern

### Before Fix (Infinite Loop)
```
GET /experts/ (every render)
GET /api/experts/{id}/progress (every render)
GET /experts/ (every render)
GET /api/experts/{id}/progress (every render)
... (continues infinitely)
```

### After Fix (Controlled Polling)
```
GET /experts/ (once on mount)
GET /api/experts/{id}/progress (initial)
... wait 2 seconds ...
GET /api/experts/{id}/progress (poll)
... wait 2 seconds ...
GET /api/experts/{id}/progress (poll)
... (continues every 2 seconds only)
```

## Testing

To verify the fix:

1. **Open Browser DevTools** (F12)
2. **Go to Network Tab**
3. **Load Dashboard**
4. **Observe API Calls**:
   - Should see ONE `/experts/` call on initial load
   - Should see `/progress` calls every 2 seconds only
   - Should NOT see continuous `/experts/` calls

## Additional Optimizations

### Stop Polling When No Active Progress

You can further optimize by stopping the polling when there are no active progress records:

```typescript
useEffect(() => {
  if (experts.length === 0) return
  
  // Only poll if there are active progress records
  const hasActiveProgress = Object.keys(expertProgress).length > 0
  if (!hasActiveProgress) return
  
  const progressInterval = setInterval(() => {
    fetchProgressForExperts()
  }, 2000)
  
  return () => clearInterval(progressInterval)
}, [experts.length, expertProgress])
```

### Use WebSocket for Real-time Updates

For production, consider using WebSocket instead of polling:

```typescript
// Future enhancement
const ws = new WebSocket('ws://localhost:8000/ws/progress')
ws.onmessage = (event) => {
  const progress = JSON.parse(event.data)
  setExpertProgress(prev => ({
    ...prev,
    [progress.expert_id]: progress
  }))
}
```

## Summary

The infinite loop was fixed by:
1. Separating initial fetch from polling logic
2. Using `experts.length` instead of `experts` as dependency
3. Optimizing state updates to only occur when needed
4. Adding initial progress fetch before starting interval

The system now works correctly with controlled, predictable API calls every 2 seconds.
