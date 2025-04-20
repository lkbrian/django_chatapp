
### 💬 **Chat App Summary**

You're building a **real-time chat application** using **Django**, with support for JWT authentication and WebSocket communication.

---

### 🔐 **Authentication**
- **User Model:** Django’s built-in `User` model.
- **Authentication Method:** JWT (JSON Web Tokens) using `djangorestframework-simplejwt`.
- **Login Endpoints:**
  - `/api/token/` – obtain access and refresh tokens.
  - `/api/token/refresh/` – refresh expired access tokens.

---

### 🧱 **Models**

#### `ChatRoom`
- `title` (string)
- `description` (text)
- `created_by` (User)
- `created_at` (datetime)
- `updated_at` (datetime)

#### `Message`
- `content` (text)
- `user` (User)
- `room` (ForeignKey to ChatRoom)
- `created_at` (datetime)
- `updated_at` (datetime)

---

### 🔁 **API Endpoints**
- CRUD operations for `ChatRoom` and `Message` using Django REST Framework.
- Access is protected by JWT authentication.

---

### ⚡ **Real-time Communication**
- Uses **Django Channels** with **Redis** for WebSocket communication.
- `ChatConsumer` handles:
  - Connecting to a room via `room_id`
  - Broadcasting messages to all clients in that room
  - Receiving messages and sending them in real-time

---

### 🛠️ **Technologies Used**
- `Django`
- `Django REST Framework`
- `djangorestframework-simplejwt`
- `channels` + `channels_redis` (WebSocket support)
- `Redis` (as Channel layer backend)

---

J