# Migration Plan: JWT to Session Auth + Code Quality Improvements

## Overview

This plan covers these changes:

1. **Replace JWT with session-based cookie authentication**
2. **Move validation logic to model serializers / service layer**
3. **Overhaul logging**
4. **Fix N+1 queries**
5. **Replace monkey-patched User with custom user model**
6. **Reduce serializer duplication**
7. **Refactor `IsSelf` permission**
8. **Miscellaneous code quality fixes**

Each section lists the files to change, what to do, and the order of operations.

---

## Phase 1: Backend — Session Auth Infrastructure

### 1.1 Settings changes

**File:** `core/settings/base.py`

- Replace `rest_framework_simplejwt.authentication.JWTAuthentication` with
  `rest_framework.authentication.SessionAuthentication` as the primary auth class.
  Keep `rest_framework.authentication.TokenAuthentication` for service accounts.

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",  # service accounts
    ],
    # ... rest stays the same
}
```

- Remove `SIMPLE_JWT` configuration block entirely.
- Remove `"rest_framework_simplejwt.token_blacklist"` from `INSTALLED_APPS`.
- Add session engine backed by Redis (reuse existing Redis):

```python
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 60 * 60 * 6  # 6 hours, matches old refresh token lifetime
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "sessionid"
SESSION_SAVE_EVERY_REQUEST = True  # sliding expiration
```

- Add a Django cache backend entry for sessions using the existing Redis:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("CACHE_REDIS", default="redis://redis:6379/0"),
    },
}
```

- Add `CSRF_COOKIE_HTTPONLY = False` (frontend JS needs to read the CSRF token).
- Add `CSRF_COOKIE_SAMESITE = "Lax"`.
- Add `CSRF_COOKIE_SECURE = True`.

**File:** `core/settings/debug.py`

- Remove `SIMPLE_JWT` overrides (5-day access token, etc.).
- Set `SESSION_COOKIE_SECURE = False` for local HTTP development.
- Set `CSRF_COOKIE_SECURE = False`.

**File:** `core/settings/test.py`

- Remove `SIMPLE_JWT` overrides.
- Set `SESSION_ENGINE = "django.contrib.sessions.backends.db"` for test isolation.

### 1.2 CSRF handling for SPA

Since both frontends are served from the same origin (Django serves the React
builds), `SameSite=Lax` cookies work naturally. The frontends need to:

1. Read the `csrftoken` cookie.
2. Send it as the `X-CSRFToken` header on mutating requests (POST/PUT/PATCH/DELETE).

DRF's `SessionAuthentication` enforces CSRF automatically.

**Alternative (simpler):** If you want to skip CSRF entirely for the API, create a
custom session auth class:

```python
# common/rest_framework/authentication.py
from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # skip CSRF — SameSite cookie provides equivalent protection
```

This is safe when `SESSION_COOKIE_SAMESITE = "Lax"` or `"Strict"` and the API is
same-origin. Use this only if you want to avoid CSRF token management in the frontend.

### 1.3 New login endpoint

**File:** `api/v1/login/views.py` — rewrite

Replace `TokenObtainPairOAuth2View` and `TokenBlacklistView` with:

```python
from django.contrib.auth import login, logout
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT

class OAuth2LoginView(GenericAPIView):
    """
    Accepts an OAuth2 code + provider, completes the OAuth2 flow,
    creates a Django session, and returns user profile data.
    """
    permission_classes = [IsNotAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        serializer = OAuth2LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        # Return user profile data that the frontend previously got from the JWT
        profile_serializer = SessionUserSerializer(user, context={"request": request})
        return Response(profile_serializer.data, status=HTTP_200_OK)


class LogoutView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logout(request)
        response = Response(status=HTTP_204_NO_CONTENT)
        response.delete_cookie("sessionid")
        return response
```

**File:** `api/v1/login/serializers.py` — rewrite

```python
class OAuth2LoginSerializer(Serializer):
    code = CharField()
    provider = CharField()

    def validate(self, attrs):
        if attrs["provider"] not in settings.SOCIAL_AUTH_PROVIDERS:
            raise ValidationError({"provider": _("Invalid provider.")})

        request = self.context["request"]
        decorate_request(request, attrs["provider"])

        # Reuse existing redirect_uri logic (origin sniffing)
        # ... (keep the existing origin/redirect_uri block from current serializer)

        request.backend.REDIRECT_STATE = False
        request.backend.STATE_PARAMETER = False
        user = request.backend.complete(request=request)

        if isinstance(user, HttpResponse):
            raise AuthException(attrs["provider"], user)

        return {"user": user}


class SessionUserSerializer(ModelSerializer):
    """
    Returns the data the frontend needs. Replaces JWT custom claims.
    """
    avatar_url = CharField(source="userprofile.avatar_url", read_only=True)
    role = CharField(read_only=True)
    groups = SlugRelatedField(many=True, read_only=True, slug_field="name")
    name = SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name", "role", "groups", "avatar_url")

    def get_name(self, obj):
        return obj.get_full_name_eastern_order()
```

### 1.4 New "me" endpoint for session refresh

The frontend currently decodes the JWT to get user data (name, role, avatar, groups).
With sessions, it needs an endpoint to fetch this on page load.

**File:** `api/v1/me/views.py`

The existing `MeViewSet` already serves this purpose. No changes needed — the
frontend will call `GET /api/v1/me/me/` on page load instead of decoding the JWT.

### 1.5 Update login URLs

**File:** `api/v1/login/urls.py`

```python
from django.urls import path
from api.v1.login.views import OAuth2LoginView, LogoutView

urlpatterns = [
    path("login/social", OAuth2LoginView.as_view(), name="social_login"),
    path("logout", LogoutView.as_view(), name="logout"),
    # Remove: login/refresh — no longer needed
]
```

### 1.6 Update ban signal

**File:** `common/signals.py`

Remove the JWT token blacklisting loop. With sessions, banning is simpler:

```python
from django.contrib.sessions.backends.cache import SessionStore

@receiver(post_save, sender=Ban)
def post_save_ban(sender, instance, **kwargs):
    instance.receiver.is_active = False
    instance.receiver.is_staff = False
    instance.receiver.is_superuser = False
    instance.receiver.groups.clear()
    instance.receiver.save()
    # Django's auth middleware automatically rejects inactive users on next request.
    # Optionally flush all sessions for this user if using DB sessions,
    # but with is_active=False the session auth check fails anyway.
```

Remove imports: `RefreshToken`, `TokenError` from `rest_framework_simplejwt`.

### 1.7 Fix the Microsoft avatar problem

**File:** `common/social_core/pipeline.py` — `get_avatar()` function

Stop storing base64 data. Instead, proxy the avatar or use a smaller size:

Option A — Store a placeholder URL and serve via a backend endpoint:

```python
# In pipeline.py — get_avatar()
elif backend.name == "microsoft-graph":
    # Just flag that Microsoft avatar is available. Serve via proxy endpoint.
    user.userprofile.avatar["microsoft-graph"] = True
```

Then add a lightweight proxy view:

```python
# api/v1/me/views.py
class AvatarProxyView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        social = request.user.social_auth.filter(provider="microsoft-graph").first()
        if not social:
            return Response(status=404)
        token = social.extra_data.get("access_token")
        resp = requests.get(
            "https://graph.microsoft.com/v1.0/me/photos/48x48/$value",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return HttpResponse(resp.content, content_type="image/jpeg")
```

Option B (simpler) — Use a much smaller photo size and keep base64:

```python
# Use 48x48 instead of 504x504 — ~2-3 KB instead of 50-100 KB
resp = requests.get(
    "https://graph.microsoft.com/v1.0/me/photos/48x48/$value",
    ...
)
```

**Recommendation:** Option B is simpler and since the avatar is no longer in a JWT
(just a DB field), the size matters less. But 504x504 base64 in the DB is still
wasteful — use 96x96 as a reasonable middle ground.

### 1.8 Remove JWT dependencies

**File:** `requirements.txt` / `pyproject.toml`

Remove:

- `djangorestframework-simplejwt`

Keep:

- `social-auth-app-django` (still needed for OAuth2)

### 1.9 Database migration

Create a migration to drop the simplejwt token tables:

```bash
python manage.py migrate token_blacklist zero  # removes token_blacklist tables
```

Then remove `rest_framework_simplejwt.token_blacklist` from `INSTALLED_APPS`.

### 1.10 Files to delete or gut

| File                            | Action                                      |
| ------------------------------- | ------------------------------------------- |
| `api/v1/login/serializers.py`   | Rewrite (remove all JWT serializer classes) |
| `api/v1/login/views.py`         | Rewrite (remove TokenBlacklistView)         |
| `api/v1/login/urls.py`          | Remove refresh endpoint                     |
| `common/social_core/helpers.py` | Remove `InvalidToken`/`TokenError` imports  |

---

## Phase 2: Frontend — Switch to Cookie Auth

### 2.1 Frontend (`frontend/`)

**File:** `src/api/apiUtils.js`

- Remove the `Authorization: Bearer ...` request interceptor.
- Remove the entire 401 → refresh token → retry logic.
- Add `withCredentials: true` to the axios instance so cookies are sent.
- Add CSRF token handling:

```javascript
import Cookies from 'js-cookie'; // or read document.cookie manually

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    config.headers['X-CSRFToken'] = Cookies.get('csrftoken');
  }
  return config;
});

// Response interceptor: on 401/403 redirect to /login (no refresh logic)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);
```

If using the CSRF-exempt session auth from 1.2, skip the `X-CSRFToken` header.

**File:** `src/helpers/authenticationHelper.js`

- Remove all localStorage token management (`access_token`, `refresh_token`, `refresh_exp`).
- `isAuthenticated()` should check for user data in state/context, not localStorage.
- On app load, call `GET /api/v1/me/me/` to check if the session is valid and get user data.

**File:** `src/api/loginApi.js`

- `loginSocial()` calls `POST /api/v1/login/social` — same as before, but the
  response now returns user profile data instead of tokens.
- Remove `loginRefresh()` entirely.
- Store returned user data (name, role, avatar, groups) in React state/context
  instead of localStorage.
- `logoutUser()` calls `POST /api/v1/logout` — same endpoint, but no refresh token
  in the body.

**File:** `src/views/LoginPage/LoginPage.jsx`

- `handleLogin()`: after successful login response, store the returned user profile
  data in React context. Remove JWT decoding (`jwt-decode`).

**File:** `src/components/AuthenticatedRoute` (or equivalent)

- Check auth by looking at React context (populated from `/me/me/` on app load),
  not localStorage tokens.

### 2.2 Frontend-Admin (`frontend-admin/`)

Same changes as above, applied to the TypeScript equivalents:

| Frontend file                         | Frontend-Admin equivalent                  |
| ------------------------------------- | ------------------------------------------ |
| `src/api/apiUtils.js`                 | `src/api/http.ts`                          |
| `src/helpers/authenticationHelper.js` | `src/helpers/LocalStorageHelper.ts`        |
| `src/api/loginApi.js`                 | Equivalent login API module                |
| `LoginPage.jsx`                       | Login page component                       |
| `AuthenticatedRoute`                  | `src/providers/AuthenticationProvider.tsx` |

### 2.3 Remove frontend dependencies

Both frontends can remove:

- `jwt-decode` — no longer decoding JWTs

---

## Phase 3: Validation Restructuring

### 3.1 Principle

- **Serializers** own data shape: field types, required fields, format.
- **Models** own business rules: `clean()` methods, validators.
- **Services** own orchestration: create object + send email + calendar event.

### 3.2 Extract service layer

Create `video_requests/services.py`:

```python
def create_request(*, data, user, comment_text=None):
    """
    Creates a Request, optionally adds a comment, sends notifications,
    and creates a calendar event.
    """
    request_obj = Request.objects.create(**data, requested_by=user)

    if comment_text:
        Comment.objects.create(
            request=request_obj,
            author=user,
            text=comment_text,
            internal=False,
        )

    # Send email notifications
    email_staff_new_request.delay(request_obj.id)

    # Create calendar event
    create_calendar_event.delay(request_obj.id)

    return request_obj


def update_request(*, request_obj, data, user):
    """Updates a request, handles status changes, notifications."""
    # ... extract from RequestAdminUpdateSerializer.update()


def create_comment(*, request_obj, author, text, internal=False):
    """Creates a comment and sends notifications."""
    comment = Comment.objects.create(
        request=request_obj, author=author, text=text, internal=internal
    )
    if not Ban.objects.filter(receiver=request_obj.requester).exists():
        email_user_new_comment.delay(request_obj.id, comment.id)
    return comment
```

### 3.3 Consolidate duplicated `create_comment()`

Currently duplicated in three serializers:

- `api/v1/requests/requests/serializers.py` — `RequestCreateSerializer.create()`
- `api/v1/admin/requests/requests/serializers.py` — `RequestAdminCreateSerializer.create()`
- `api/v1/external/sch_events/serializers.py` — `RequestExternalSchEventsCreateSerializer.create()`

All three should call `services.create_comment()`.

### 3.4 Move model validation to models

**File:** `video_requests/models.py`

The `Request.clean()` already validates date ordering — this is good. Add:

```python
class Request(models.Model):
    # ...
    def clean(self):
        if self.start_datetime and self.end_datetime:
            if self.start_datetime > self.end_datetime:
                raise ValidationError(
                    {"end_datetime": [_("Must be later than the start of the event.")]}
                )
            if self.deadline and self.end_datetime.date() >= self.deadline:
                raise ValidationError(
                    {"deadline": [_("Must be later than the end of the event.")]}
                )
```

(Note: simplified from `not (a <= b)` to `a > b`)

### 3.5 Slim down API serializers

After extracting services, serializer `.create()` methods become:

```python
class RequestCreateSerializer(ModelSerializer):
    class Meta:
        model = Request
        fields = (...)

    def create(self, validated_data):
        comment_text = validated_data.pop("comment", None)
        return create_request(
            data=validated_data,
            user=self.context["request"].user,
            comment_text=comment_text,
        )
```

---

## Phase 4: Logging Overhaul

### 4.1 Add request logging middleware

**New file:** `common/middleware.py`

```python
import logging
import time

logger = logging.getLogger("api.access")

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        if response.status_code >= 400:
            user_id = getattr(request.user, "id", None)
            logger.warning(
                "%(method)s %(path)s %(status)s %(duration).0fms user=%(user)s ip=%(ip)s",
                {
                    "method": request.method,
                    "path": request.get_full_path(),
                    "status": response.status_code,
                    "duration": duration_ms,
                    "user": user_id,
                    "ip": request.META.get("REMOTE_ADDR"),
                },
            )

        return response
```

Add to `MIDDLEWARE` in `base.py` (after `AuthenticationMiddleware` so `request.user`
is available).

### 4.2 Log permission denials

**File:** `common/rest_framework/exception.py`

```python
def exception_handler(exception, context):
    if isinstance(exception, DjangoValidationError):
        exception = DRFValidationError(detail=get_error_detail(exception))

    response = drf_exception_handler(exception, context)

    if response is not None and response.status_code in (401, 403):
        request = context.get("request")
        LOG.warning(
            "Permission denied: %s %s user=%s status=%s detail=%s",
            request.method if request else "?",
            request.get_full_path() if request else "?",
            getattr(request.user, "id", None) if request else None,
            response.status_code,
            response.data,
        )

    return response
```

### 4.3 Improve external API logging

**File:** `api/v1/external/sch_events/views.py`

```python
# Before (line 24):
logger.exception("SCH Events (bejelentes.sch) bad request received.")

# After:
logger.exception(
    "SCH Events bad request: %s %s body=%s",
    request.method,
    request.get_full_path(),
    request.data,
)
```

### 4.4 Use the existing unused logger

**File:** `common/rest_framework/exception.py`

The `LOG` logger is already defined but never used. Phase 4.2 above puts it to use.

### 4.5 Settings — add structured format for API logs

**File:** `core/settings/base.py`

Add a dedicated logger for API access:

```python
LOGGING["loggers"]["api.access"] = {
    "handlers": ["console", "info"],
    "level": "WARNING",
    "propagate": False,
}
```

---

## Phase 5: Smaller Fixes (can be done anytime)

### 5.1 Fix f-string bug

**File:** `common/utilities.py:146`

```python
# Before:
return "Calendar event for {request.title} was deleted successfully."
# After:
return f"Calendar event for {request.title} was deleted successfully."
```

### 5.2 Wrap model choice labels in gettext

**File:** `video_requests/models.py`

```python
class Statuses(models.IntegerChoices):
    DENIED = 0, _("Denied")
    REQUESTED = 1, _("Requested")
    # ...
```

Same for `Video.Statuses` and `Todo.Statuses`.

### 5.3 Add db_index on frequently filtered fields

```python
status = models.PositiveSmallIntegerField(choices=Statuses, default=..., db_index=True)
```

Apply to `Request.status` and `Video.status`.

### 5.4 Fix related_name values

```python
responsible = models.ForeignKey(User, related_name="responsible_requests", ...)
requester = models.ForeignKey(User, related_name="requested_requests", ...)
requested_by = models.ForeignKey(User, related_name="submitted_requests", ...)
```

### 5.5 Remove redundant unique=True on Ban.receiver

```python
receiver = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
# Remove unique=True — primary_key already implies it
```

### 5.6 Modernize settings paths

Replace `os.path.join(...)` with `pathlib.Path` in `core/settings/base.py`.

### 5.7 Update stale doc comments in settings

**File:** `core/settings/base.py`

The file header and inline comments still reference Django 2.2 / 3.0:

```python
# Before:
"""Generated by 'django-admin startproject' using Django 2.2."""
# https://docs.djangoproject.com/en/3.0/topics/settings/

# After: remove the "Generated by" line, update URLs to current Django version
# https://docs.djangoproject.com/en/6.0/topics/settings/
```

### 5.8 Fix fragile `save_user_profile` signal

**File:** `common/signals.py`

The current `save_user_profile` signal runs on every `User.save()`, including right
after `create_user_profile` (which just created the profile). It also crashes if
a `UserProfile` doesn't exist yet for some edge-case code path.

```python
# Before:
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

# After — merge into create signal and guard:
@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    elif hasattr(instance, 'userprofile'):
        instance.userprofile.save()
```

Remove the separate `create_user_profile` and `save_user_profile` signals.

### 5.9 Fix `full_clean()` with `exclude` in `Request.save()`

**File:** `video_requests/models.py`

```python
# Current:
def save(self, *args, **kwargs):
    if not self.deadline:
        self.deadline = (self.end_datetime + timedelta(weeks=3)).date()
    self.full_clean(exclude=["additional_data"])
    super().save(*args, **kwargs)
```

The `exclude=["additional_data"]` means the JSON schema validator is bypassed on
direct saves. If the schema matters, validate it. If it doesn't, remove the validator
from the field. DRF already calls serializer validation before save, but management
commands and signals bypass serializers.

**Recommendation:** Remove the exclude — validate `additional_data` always:

```python
def save(self, *args, **kwargs):
    if not self.deadline:
        self.deadline = (self.end_datetime + timedelta(weeks=3)).date()
    self.full_clean()
    super().save(*args, **kwargs)
```

If there are code paths that save with incomplete `additional_data`, fix those
code paths instead of skipping validation.

### 5.10 Cap `MemoryCache` growth

**File:** `common/utilities.py`

The Google API `MemoryCache` uses a class-level dict that grows unboundedly in
long-running Celery workers:

```python
class MemoryCache(Cache):
    _CACHE = {}  # never evicted
```

Replace with an LRU cache or add a size limit:

```python
from functools import lru_cache

class MemoryCache(Cache):
    _CACHE = {}
    _MAX_SIZE = 128

    def get(self, url):
        return self._CACHE.get(url)

    def set(self, url, content):
        if len(self._CACHE) >= self._MAX_SIZE:
            # Evict oldest entry
            self._CACHE.pop(next(iter(self._CACHE)))
        self._CACHE[url] = content
```

### 5.11 Rename `Request.type` field

**File:** `video_requests/models.py`

`type` shadows Python's builtin. Rename to `request_type`:

```python
request_type = models.CharField(max_length=50, db_column="type")
```

Using `db_column="type"` avoids a data migration. Update all references in
serializers, views, templates, and frontend code.

---

## Phase 6: Fix N+1 Queries

### 6.1 `SerializerMethodField` queries in list views

These fields run a query per object when serializing lists:

**`VideoListRetrieveSerializer.get_rating()`** — `api/v1/requests/videos/serializers.py`

```python
# Current — N+1:
def get_rating(self, obj):
    return obj.ratings.filter(author=self.context["request"].user).first()
```

Fix with `Prefetch` in the viewset's queryset:

```python
# In VideoViewSet.get_queryset():
from django.db.models import Prefetch

def get_queryset(self):
    return Video.objects.prefetch_related(
        Prefetch(
            "ratings",
            queryset=Rating.objects.filter(author=self.request.user),
            to_attr="user_ratings",
        )
    )

# In serializer:
def get_rating(self, obj):
    ratings = getattr(obj, "user_ratings", [])
    return RatingSerializer(ratings[0]).data if ratings else None
```

**`VideoAdminListSerializer.get_rated()`** — `api/v1/admin/requests/videos/serializers.py`

Same pattern — use `Prefetch` with `to_attr` and check the prefetched list.

**`RequestAdminRetrieveSerializer.get_videos_edited()`** — `api/v1/admin/requests/requests/serializers.py`

```python
# Current — iterates all videos:
def get_videos_edited(self, obj):
    return obj.videos.exists() and all(
        video.status >= Video.Statuses.EDITED for video in obj.videos.all()
    )

# Fix — use annotation:
from django.db.models import Min

# In queryset:
queryset = Request.objects.annotate(
    min_video_status=Min("videos__status"),
    has_videos=Exists(Video.objects.filter(request=OuterRef("pk"))),
)

# In serializer:
def get_videos_edited(self, obj):
    return obj.has_videos and obj.min_video_status >= Video.Statuses.EDITED
```

### 6.2 `UserAdminViewSet.worked_on()`

**File:** `api/v1/admin/users/views.py`

This method (~80 lines) runs three separate queryset iterations building dicts
manually. Replace with a single annotated queryset:

```python
from django.db.models import Q, Exists, OuterRef

def worked_on(self, request, pk=None):
    user = self.get_object()
    requests = (
        Request.objects.filter(
            Q(responsible=user) |
            Q(crew__member=user) |
            Q(videos__editor=user)
        )
        .filter(start_datetime__range=(start_date, end_date))
        .distinct()
        .select_related("responsible", "requester")
        .order_by("-start_datetime")
    )
    serializer = UserAdminWorkedOnSerializer(requests, many=True)
    return Response(serializer.data)
```

### 6.3 Add `select_related` / `prefetch_related` to viewset querysets

Review all viewsets and add appropriate prefetching. Key ones:

```python
# RequestViewSet
def get_queryset(self):
    return Request.objects.select_related(
        "responsible", "requester", "requested_by"
    ).prefetch_related("crew__member", "videos", "comments__author")

# CommentViewSet
def get_queryset(self):
    return Comment.objects.select_related("author")

# RequestAdminViewSet
def get_queryset(self):
    return Request.objects.select_related(
        "responsible", "requester", "requested_by",
        "responsible__userprofile", "requester__userprofile",
    ).prefetch_related("crew__member", "videos__editor", "todos")
```

---

## Phase 7: Replace Monkey-Patched User with Custom User Model

### 7.1 Why

`common/utilities.py` adds methods to Django's `User` at runtime via
`User.add_to_class()`. IDEs can't resolve these, type checkers can't see them, and
they're invisible to anyone reading the User model.

### 7.2 Create custom user model

**New file:** `common/models.py` — add `CustomUser`:

```python
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):

    class Meta:
        # Keep using the same DB table to avoid a complex data migration
        db_table = "auth_user"

    @property
    def role(self):
        if self.is_admin:
            return "admin"
        elif self.is_staff:
            return "staff"
        return "user"

    @property
    def is_admin(self):
        return self.is_staff and (
            self.groups.filter(name=settings.ADMIN_GROUP).exists()
            or self.is_superuser
        )

    @property
    def is_service_account(self):
        return self.groups.filter(name=settings.SERVICE_ACCOUNTS_GROUP).exists()

    def get_full_name_eastern_order(self):
        return f"{self.last_name} {self.first_name}".strip()
```

### 7.3 Settings

**File:** `core/settings/base.py`

```python
AUTH_USER_MODEL = "common.User"
```

### 7.4 Update all imports

Replace all `from django.contrib.auth.models import User` with
`from django.conf import settings` and use `settings.AUTH_USER_MODEL` in models
(for ForeignKey) or `from common.models import User` in code.

In models, foreign keys should use the string reference:

```python
# Before:
from django.contrib.auth.models import User
requester = models.ForeignKey(User, ...)

# After:
requester = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
```

### 7.5 Remove monkey-patching

**File:** `common/utilities.py`

Remove these lines:

```python
User.add_to_class("role", role)
User.add_to_class("get_full_name_eastern_order", get_full_name_eastern_order)
User.add_to_class("is_admin", is_admin)
User.add_to_class("is_service_account", is_service_account)
```

And the standalone function/property definitions that were being patched in.

### 7.6 Migration strategy

Since `AbstractUser` has the same fields as `auth.User`, and we set
`db_table = "auth_user"`, the database doesn't change. But Django's migration
system needs a careful transition.

**`SeparateDatabaseAndState` does not work here.** Once `AUTH_USER_MODEL` points
away from `auth.User`, that model's `_meta.swapped` is truthy, so `can_migrate()`
returns `False` and `auth/0001` stops creating the `auth_user` table. A state-only
migration would therefore leave every fresh database — CI, tests, new developers —
with no user table at all.

What was done instead:

1. Create `common.User` with `db_table = "auth_user"`, redeclaring the `groups` and
   `user_permissions` M2M fields with `db_table="auth_user_groups"` /
   `db_table="auth_user_user_permissions"` so the join tables keep their names.
2. Set `AUTH_USER_MODEL = "common.User"`.
3. Add the `CreateModel("User", …)` operation to the **existing**
   `common/0001_initial.py`, ahead of the other models, and point that file's two
   literal `to="auth.user"` references at `settings.AUTH_USER_MODEL`.
4. Add `common/0004_move_user_content_type.py`, moving the `auth|user` content type
   to `common|user` so the permission rows and admin log entries attached to it are
   not orphaned next to a freshly created one.

Editing an applied migration is safe here because `django_migrations` stores only
`(app, name, applied)` — no checksum — and the schema the edit describes already
exists. The result:

- **Existing databases**: `common.0001` is already recorded, so it never re-runs. No
  `--fake`, no manual SQL. Only the new migrations apply.
- **Fresh databases**: `common.0001` creates `auth_user` in the right order.
- **Dependency graph**: `swappable_dependency` from every other app resolves to
  `("common", "__first__")` — that is `common.0001`, which is already applied, so
  `check_consistent_history()` passes. (Django's `MigrationLoader.check_key()`
  ignores `__first__` self-references, so `common.0001` does not depend on itself.)

Verified by building a database from the pre-change code in a temporary worktree,
seeding a user with a group and a permission, then migrating with the new code:
only the content-type migration ran, the tables and content type ID were unchanged,
and the permissions survived without duplicates.

One new footgun: migration state now says `common.0001` created `auth_user`, so
`manage.py migrate common zero` would drop the user table rather than leaving it to
the auth app. Never a normal operation, but worth remembering before squashing
`common`'s migrations.

Django's docs on the general problem:
https://docs.djangoproject.com/en/6.0/topics/auth/customizing/#changing-to-a-custom-user-model-mid-project

---

## Phase 8: Reduce Serializer Duplication

### 8.1 Problem

Comment, Rating, and Video serializers are near-duplicated between user-facing
(`api/v1/requests/`) and admin (`api/v1/admin/requests/`) endpoints. The admin
versions add a few fields but share 90%+ of the code.

### 8.2 Solution — base serializer inheritance

For each duplicated pair, create a base serializer in `common/` or alongside the
model, and have both user and admin versions inherit from it:

```python
# common/serializers.py (or video_requests/serializers.py)
class BaseCommentSerializer(ModelSerializer):
    author_name = CharField(source="author.get_full_name_eastern_order", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "author", "author_name", "text", "created", "internal")
        read_only_fields = ("id", "author", "created")


# api/v1/requests/comments/serializers.py
class CommentListRetrieveSerializer(BaseCommentSerializer):
    pass  # user-facing: same fields


# api/v1/admin/requests/comments/serializers.py
class CommentAdminListRetrieveSerializer(BaseCommentSerializer):
    class Meta(BaseCommentSerializer.Meta):
        fields = BaseCommentSerializer.Meta.fields + ("history",)
```

Apply the same pattern to:

- `RatingRetrieveSerializer` / `RatingAdminListRetrieveSerializer`
- `VideoListRetrieveSerializer` / `VideoAdminListSerializer`

---

## Phase 9: Refactor `IsSelf` Permission

### 9.1 Problem

**File:** `common/rest_framework/permissions.py`

`IsSelf` checks 5+ model types in one long if/elif chain. It silently returns
`False` for unknown types, which means adding a new model requires editing this
permission class.

### 9.2 Solution — model-declared ownership

Option A — Convention-based:

```python
class IsOwner(IsAuthenticated):
    """
    Each model declares its owner via an `owner_field` or `get_owner()` method.
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "get_owner"):
            return obj.get_owner() == request.user
        return False
```

Then on each model:

```python
class Comment(AbstractComment):
    def get_owner(self):
        return self.author

class Request(models.Model):
    def get_owner(self):
        return self.requester

class Video(models.Model):
    def get_owner(self):
        return self.request.requester
```

Option B — Per-model permissions (more explicit):

```python
class IsRequestRequester(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return obj.requester == request.user

class IsCommentAuthor(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
```

**Recommendation:** Option A is cleaner if you want a single reusable permission.
Option B is more explicit and easier to reason about per-view. Either way, it
replaces the fragile isinstance chain.

---

## Execution Order

```
1. Phase 5 (small fixes)           — no dependencies, safe to do first
2. Phase 4 (logging)               — no dependencies on other changes
3. Phase 6 (N+1 queries)           — no dependencies on other changes
4. Phase 8 (serializer dedup)      — no dependencies, simplifies Phase 3
5. Phase 9 (permission refactor)   — no dependencies on other changes
6. Phase 3 (validation/services)   — easier after Phase 8
7. Phase 7 (custom user model)     — do before auth migration, touches many files
8. Phase 1 (backend auth)          — must be deployed together with Phase 2
9. Phase 2 (frontend auth)         — must be deployed together with Phase 1
```

Phases 1+2 must be deployed atomically (single release). Consider a feature flag or
maintenance window. All other phases are independent and can be merged separately.

Phase 7 (custom user model) is the riskiest standalone change — do it on a
separate branch with thorough testing. It should land before Phases 1+2 since the
auth migration also touches user-related code.

---

## Migration Checklist

### Phase 5: Small fixes

- [x] Fix f-string bug in `common/utilities.py`
- [x] Wrap status labels in `_()`
- [x] Add `db_index=True` to status fields + migration
- [x] Fix `related_name` values + update any queryset references
- [x] Remove redundant `unique=True` on `Ban.receiver`
- [x] Modernize `os.path` to `pathlib.Path`
- [x] Update stale Django 2.2/3.0 doc comments in settings
- [x] Fix fragile `save_user_profile` signal (merge with create signal)
- [x] Simplify `Request.clean()` conditionals (kept `exclude=["additional_data"]`)
- [x] Cap `MemoryCache` growth in `common/utilities.py`
- [ ] Rename `Request.type` → `Request.request_type` (with `db_column="type"`) — deferred to separate PR

### Phase 4: Logging

- [x] Add `RequestLoggingMiddleware` (`common/middleware.py`)
- [x] Log 403 permission denials in exception handler (`common/rest_framework/exception.py`)
- [x] Improve SCH Events external API error logging with request context
- [x] Add `api.access` logger config, silence `django.request` default WARNING logs
- [x] Fix `debug.py` overwriting all logger configs (used `LOGGING["loggers"][""]` instead of `LOGGING.update`)
- [x] Standardize logger naming: `logger = logging.getLogger(__name__)` everywhere
- [x] Replace root `logging.*()` calls with module loggers (`sync_bss_users.py`, `pipeline.py`)
- [x] Add logging to silent exception handlers (`helpers.py`, `pipeline.py`, `admin.py`)
- [x] Switch from f-strings to lazy `%s` formatting in log calls
- [ ] Add `environment` and `release` to Sentry config in `production.py` and `staging.py`
- [ ] Add `traces_sample_rate` to `staging.py` (missing, production has 0.15)

### Phase 6: N+1 queries

- [x] Fix `VideoListRetrieveSerializer.get_rating()` — `Prefetch` with `to_attr="user_ratings"`
- [x] Fix `VideoAdminListSerializer.get_rated()` — `Prefetch` with `to_attr="user_ratings"`
- [x] Fix `RequestAdminRetrieveSerializer.get_videos_edited()` — use `len()` on prefetched cache instead of `.exists()`
- [x] Fix `UserAdminViewSet.worked_on()` — add `select_related("request")`, replace `__dict__` with explicit dicts
- [x] Reviewed all other viewsets — existing prefetching is adequate

### Phase 8: Serializer deduplication

- [x] Reviewed all serializer pairs — duplication is minimal (a few field declarations) and the explicit, self-contained style is more readable than inheritance. Skipped.

### Phase 9: Permission refactor

- [x] Add `get_owner()` method to Request, Video, Comment, Rating, Todo models
- [x] Replace `IsSelf` isinstance chain with `get_owner()` lookup
- [x] Views unchanged — `IsSelf` name kept, just simplified internally

### Phase 3: Validation / services

- [x] Create `video_requests/services.py`
- [x] Extract `create_comment()` service (replaced 3 duplicate static methods)
- [x] Move avatar provider validation from serializer to `UserProfile.clean()` (now
      `User.clean()` — `UserProfile` was merged into `User` in Phase 7)
- [x] Move email uniqueness validation to model — partial, case-insensitive
      `UniqueConstraint` on `User.email`
- [x] Simplify `Request.clean()` conditionals (done in Phase 5)

### Phase 7: Custom user model

- [x] Create `common.User` extending `AbstractUser` (with `db_table = "auth_user"`)
- [x] Set `AUTH_USER_MODEL = "common.User"` in settings
- [x] ~~Create `SeparateDatabaseAndState` migration~~ — not viable, see 7.6. Added
      `CreateModel` to the existing `common/0001_initial.py` plus
      `0004_move_user_content_type`
- [x] Update all `ForeignKey(User, ...)` to use `settings.AUTH_USER_MODEL`
- [x] Update all `from django.contrib.auth.models import User` imports
- [x] Remove monkey-patching from `common/utilities.py`
- [x] Add `common.user` to `CACHEOPS` — the existing `auth.*` rule no longer matches
      the user model
- [x] Merge `UserProfile` into `User` (`avatar`, `phone_number`) and drop the
      `create_or_save_user_profile` signal. The API keeps its nested `profile`
      object via `source="*"`, so no frontend change
- [x] Add `Roles` TextChoices, `is_banned`, and unusable passwords for the
      sentinel / anonymous / system accounts (`0006`)
- [x] Rename `ExtendedUserAdmin` → `UserAdmin`, `validate_profile_avatar` →
      `validate_avatar`, `USER_PROFILE_AVATAR_SCHEMA` → `USER_AVATAR_SCHEMA`
- [x] Cache the group names on the user. `is_admin` / `is_service_account` / `role`
      each ran their own `groups.filter(...).exists()`: 3 queries, none of them
      cached (cacheops `auth.*` covers `fetch`/`get`, not `exists`) and none of them
      able to use `prefetch_related("groups")`. A `group_names` cached property read
      through `groups.all()` brings that to 1 query, or 0 on a prefetched queryset.
      Call `invalidate_group_names()` after changing a user's groups — the ban signal
      and the BSS group sync both do
- [x] Finish the `related_name` cleanup Phase 5 started on `Request`:
      `ban_creator` → `created_bans`, `todo_creator` → `created_todos`, and
      `Todo.assignees` gains `assigned_todos` (was the default `todo_set`)

#### Deploy pre-check: duplicate e-mail addresses

`0007_add_unique_user_email_constraint` creates a unique index and **will fail** if
any two accounts share an address. `associate_by_email` already treats that as an
error at login time, so it may well exist in production. Check before deploying:

```sql
SELECT lower(email) AS email, count(*) AS rows, array_agg(username ORDER BY id)
FROM auth_user
WHERE email <> ''
GROUP BY lower(email)
HAVING count(*) > 1
ORDER BY 2 DESC;
```

Resolve every row this returns first. Blank addresses are exempt from the constraint,
so the sentinel / anonymous / system accounts are fine.

#### Follow-up: revisit `User.save()` validation

`User.save()` calls `full_clean()` scoped to `avatar` and `phone_number` only, with
`validate_unique=False`. That reproduces exactly what `UserProfile.save()` used to
validate, and nothing more.

A bare `full_clean()` is the obvious simplification, but it is blocked on three
things:

- `password` is `CharField(max_length=128)` with no `blank=True`, and the sentinel /
  anonymous / system accounts plus `sync_bss_users` are created through
  `get_or_create()` without one. Verified: swapping in a bare `full_clean()` fails 11
  tests, all with `{'password': ['This field cannot be blank.']}`. Migration
  `0006_set_unusable_password_on_system_accounts` fixes the existing rows, but the
  field still needs `blank=True` for future `get_or_create()` calls.
- It would start validating `username` and `email`, which arrive unchecked from the
  identity providers (`sync_bss_users` assigns `result["email"]` directly;
  `disconnect_all_other_profiles_and_change_username_on_first_bss_login` assigns
  `details["username"]` directly). Existing rows holding values that fail those
  validators would become unsaveable.
- `validate_unique=True` adds a `SELECT` to every save, including `update_last_login`
  on every login, and turns `IntegrityError` into `ValidationError`.

Worth revisiting once Phase 1 lands and the login paths are simpler.

### Phase 1: Backend auth (JWT → sessions)

- [ ] Add session/cache settings
- [ ] Update `DEFAULT_AUTHENTICATION_CLASSES`
- [ ] Create new login/logout views
- [ ] Rewrite login serializers
- [ ] Update login URLs (remove refresh)
- [ ] Simplify ban signal. Note: the signal clearing `is_staff`, `is_superuser` and
      the group membership is deliberate, not a bug — `set_groups_and_permissions_for_staff`
      restores all three from BSS on the next `bss-login`, so an unbanned staff member
      only has to log in again. Keep that behaviour when simplifying
- [ ] Fix Microsoft avatar (smaller size, no base64 in JWT)
- [ ] Remove `SIMPLE_JWT` config
- [ ] Remove `token_blacklist` from `INSTALLED_APPS`
- [ ] Drop token_blacklist DB tables via migration
- [ ] Remove `djangorestframework-simplejwt` dependency

### Phase 2: Frontend auth

- [ ] Update axios — `withCredentials: true`, remove `Authorization` header
- [ ] Add CSRF token handling (or use exempt auth class)
- [ ] Remove token refresh interceptor logic
- [ ] Replace localStorage token storage with React context
- [ ] Call `GET /me/me/` on app load for session validation
- [ ] Update login handler — store response data, not decoded JWT
- [ ] Update logout — no refresh token in body
- [ ] Update `AuthenticatedRoute` / `AuthenticationProvider`
- [ ] Remove `jwt-decode` dependency
- [ ] Apply same changes to `frontend-admin`
- [ ] Flatten the `profile` object into plain user fields. `avatar`, `avatar_url` and
      `phone_number` are ordinary `User` fields since Phase 7; the nesting survives
      only because `UserProfileSerializer` is attached with `source="*"` to keep the
      wire format stable. Dropping it changes `GET`/`PATCH /me/me/` and the admin
      user endpoints, so it has to land with the frontend work rather than before it

### Final

- [ ] Tests: Update all auth-related tests
- [ ] Deploy Phase 1 + Phase 2 atomically
