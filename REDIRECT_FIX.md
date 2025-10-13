# Expert Creation Redirect & Progress Display Fix

## Issue

After creating an expert with files, the user was redirected to the dashboard but the progress bar was not showing up immediately.

## Root Cause

1. **No automatic redirect**: The create expert page only had a manual "Go to Dashboard" button
2. **No refresh trigger**: Dashboard didn't know a new expert was created
3. **No immediate progress fetch**: Progress polling only started based on existing experts

## Solution

### 1. Create Expert Page Changes

**Added automatic redirect with query parameter:**

```typescript
// After successful expert creation
const expertId = result.expert?.id

// Automatically redirect to dashboard after 2 seconds
setTimeout(() => {
  router.push(`/dashboard?new_expert=${expertId}`)
}, 2000)
```

**Benefits:**
- Shows success dialog for 2 seconds
- Automatically redirects to dashboard
- Passes expert ID via query parameter

### 2. Dashboard Page Changes

**Added query parameter detection:**

```typescript
const searchParams = useSearchParams()
const [newExpertId, setNewExpertId] = useState<string | null>(null)

useEffect(() => {
  // Check if we're redirected from expert creation
  const newExpert = searchParams.get('new_expert')
  if (newExpert) {
    setNewExpertId(newExpert)
    console.log('New expert created:', newExpert)
  }
  
  fetchExperts()
}, [])
```

**Added immediate progress fetch for new expert:**

```typescript
// Watch for new expert and fetch its progress immediately
useEffect(() => {
  if (newExpertId && experts.length > 0) {
    console.log('Fetching progress for new expert:', newExpertId)
    // Force immediate progress fetch for the new expert
    fetchProgressForExperts()
  }
}, [newExpertId, experts.length])
```

**Updated polling to restart on new expert:**

```typescript
useEffect(() => {
  if (experts.length === 0) return
  
  fetchProgressForExperts()
  
  const progressInterval = setInterval(() => {
    fetchProgressForExperts()
  }, 2000)
  
  return () => clearInterval(progressInterval)
}, [experts.length, newExpertId]) // Also depend on newExpertId
```

## User Flow

### Before Fix
```
1. User creates expert with files
2. Success dialog appears
3. User clicks "Go to Dashboard"
4. Dashboard loads
5. No progress bar visible (or delayed)
```

### After Fix
```
1. User creates expert with files
2. Success dialog appears (2 seconds)
3. Automatically redirects to dashboard
4. Dashboard detects new expert via query param
5. Immediately fetches expert list
6. Immediately fetches progress for new expert
7. Progress bar appears and updates every 2 seconds
8. User sees real-time progress
```

## Technical Flow

```
Create Expert Page:
  ↓
Expert Created Successfully
  ↓
Show Success Dialog (2s)
  ↓
Auto Redirect: /dashboard?new_expert={id}
  ↓
Dashboard Loads
  ↓
Detect Query Param: new_expert={id}
  ↓
Set newExpertId State
  ↓
Fetch Experts List
  ↓
Fetch Progress (triggered by newExpertId)
  ↓
Start Polling (every 2s)
  ↓
Progress Bar Appears
  ↓
Updates in Real-time
```

## Files Modified

### Frontend
1. **`app/dashboard/create-expert/page.tsx`**
   - Added `useRouter` import
   - Added automatic redirect with query parameter
   - Updated "Go to Dashboard" button to use router

2. **`app/dashboard/page.tsx`**
   - Added `useSearchParams` import
   - Added `newExpertId` state
   - Added query parameter detection
   - Added immediate progress fetch for new expert
   - Updated polling dependencies

## Testing

### Test the Fix

1. **Create an Expert**:
   ```
   - Go to /dashboard/create-expert
   - Fill in expert details
   - Upload files
   - Click "Create Expert"
   ```

2. **Observe Behavior**:
   ```
   - Success dialog appears (2 seconds)
   - Automatically redirects to /dashboard
   - New expert card appears
   - Progress bar shows immediately
   - Progress updates every 2 seconds
   ```

3. **Verify Console Logs**:
   ```
   - "New expert created: {expert_id}"
   - "Fetching progress for new expert: {expert_id}"
   - Progress API calls every 2 seconds
   ```

### Expected Results

✅ Automatic redirect after 2 seconds
✅ Dashboard shows new expert immediately
✅ Progress bar appears right away
✅ Progress updates in real-time
✅ Chat button disabled during processing
✅ Chat button enables when complete

## Additional Improvements

### Optional: Add Loading Indicator

Show a loading indicator while redirecting:

```typescript
const [isRedirecting, setIsRedirecting] = useState(false)

// After success
setIsRedirecting(true)
setTimeout(() => {
  router.push(`/dashboard?new_expert=${expertId}`)
}, 2000)
```

### Optional: Add Toast Notification

Show a toast when redirected:

```typescript
// In dashboard
useEffect(() => {
  const newExpert = searchParams.get('new_expert')
  if (newExpert) {
    toast.success('Expert created! Processing files...')
  }
}, [])
```

### Optional: Scroll to New Expert

Automatically scroll to the new expert card:

```typescript
useEffect(() => {
  if (newExpertId) {
    const element = document.getElementById(`expert-${newExpertId}`)
    element?.scrollIntoView({ behavior: 'smooth' })
  }
}, [newExpertId, experts])
```

## Summary

The fix ensures that:
1. Users are automatically redirected to dashboard after creating an expert
2. Dashboard immediately detects the new expert via query parameter
3. Progress is fetched immediately for the new expert
4. Progress bar appears right away and updates in real-time
5. User experience is smooth and intuitive

**Result**: Users now see the progress bar immediately after creating an expert, providing clear feedback that their files are being processed! 🎉
