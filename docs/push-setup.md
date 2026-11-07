# Push notifications (FCM) — setup

In-app notifications are the source of truth. FCM is a mirror.

## Backend
1. Create Firebase project → get `FCM_SERVER_KEY` (legacy server key) or service account.
2. Set env: `FCM_SERVER_KEY=...` and `ENV=prod` (rate limits only enforce in prod).
3. `PushAdapter` posts to `https://fcm.googleapis.com/fcm/send`. No key = log-only, never crashes confirm.

## Android
1. Add `google-services.json` to `android-app/app/` (Firebase Console → Android app `com.sixto.rootx`).
2. Project `build.gradle.kts`:
   ```
   classpath("com.google.gms:google-services:4.4.2")
   ```
3. App `build.gradle.kts`:
   ```
   apply plugin: "com.google.gms.google-services"
   dependencies {
       implementation("com.google.firebase:firebase-messaging:24.0.0")
       implementation("com.google.android.gms:play-services-tasks:17.2.1")
   }
   ```
4. In `PushRegistrar.fetchToken()` replace the `null` stub:
   ```kotlin
   // import com.google.firebase.messaging.FirebaseMessaging
   // import com.google.android.gms.tasks.Tasks
   val t = Tasks.await(FirebaseMessaging.getInstance().token)
   return t
   ```
   Then call `registerWithToken(t)` from MainActivity.
5. `MainActivity` already calls `PushRegistrar.registerIfAvailable()` (no-op until step 4). Backend stores via `POST /push/register`.

## Email (SMTP mirror)
Set `MAIL_HOST`, `MAIL_PORT`, `MAIL_USER`, `MAIL_PASS`, `MAIL_FROM`. `EmailAdapter` sends on payment-confirm (template-rendered). No config = log-only.

## Test
- Register token via `POST /push/register {"token":"test"}` → `GET /push/mine` shows it.
- Confirm a payment → check `GET /notifications/mine` has the template message (always works, even without FCM/SMTP).
