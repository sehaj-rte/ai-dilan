# Bcrypt Compatibility Fix

## Issue

Login was failing with error:
```
AttributeError: module 'bcrypt' has no attribute '__about__'
```

## Root Cause

- **bcrypt 5.0.0** removed the `__about__` attribute
- **passlib 1.7.4** still expects this attribute
- Incompatibility between versions

## Solution

Downgrade bcrypt to version 4.0.1 which is compatible with passlib 1.7.4:

```bash
pip install bcrypt==4.0.1
```

## Verification

```bash
# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Should return JWT token without errors
```

## Long-term Solution

Wait for passlib to release a new version compatible with bcrypt 5.x, or use an alternative like:

```python
# Alternative: Use bcrypt directly instead of passlib
import bcrypt

# Hash password
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Verify password
bcrypt.checkpw(password.encode(), hashed)
```

## Fixed!

Login should now work correctly with bcrypt 4.0.1 ✅
