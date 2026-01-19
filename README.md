# Real-Time Chat System (RTS)

RTS is a high-performance, scalable real-time messaging platform built on a microservices architecture. It supports diverse communication modes including private messaging, group chats, public/private channels, and a "Favorites" feature for self-messaging.

## Core Features
- **Real-time Communication:** Powered by WebSockets for instant message delivery.
- **Messaging Modes:**
    - **Direct Messages (DM):** One-on-one private conversations.
    - **Favorites:** A dedicated space for users to send messages to themselves.
    - **Groups:** Multi-user chats with administrative controls.
    - **Channels:** Broadcast-style rooms (Public or Private) for large audiences.
- **File Sharing:** Secure upload and download of media and documents via S3-compatible storage.
- **Presence Tracking:** Real-time online/offline status indicators.
- **Advanced Permissions:** Fine-grained access control using JWT Scopes.

---

## Technical Stack
- **Language:** Python 3.11+
- **Framework:** FastAPI (Asynchronous API and WebSockets)
- **Message Broker:** Apache Kafka (Event-driven communication)
- **Databases:** 
    - PostgreSQL (Persistent metadata and message history)
    - Redis (Session management, presence tracking, and caching)
- **Object Storage:** S3-compatible (MinIO / AWS S3) for binary data.
- **Security:** JWT Authentication with OAuth2 integration (Google/Social Login support).

---

## Architecture Overview
The system follows an **Event-Driven Architecture (EDA)**. 
- **Identity & Profiles:** `Auth Service` is the source of truth for Identity and generates the `user_id`. Upon registration (including OAuth2 flows), it emits a `UserCreated` event to Kafka.
- **Eventual Consistency:** `User Service` consumes registration events to initialize user profiles.
- **Message Flow:** The `WebSocket Gateway` handles client connections, while the `Message Service` processes and persists data. The `Notification Service` ensures users are alerted to new activity even when not actively in a specific chat.

---

## Microservices Status

| Service | Responsibility | Status |
| :--- | :--- | :--- |
| **API Gateway** | Entry point, Request routing, JWT validation, Rate limiting. | 🏗️ In Progress |
| **Auth Service** | Identity management, Password hashing, JWT issuance, OAuth2/Social login. | ✅ Operational |
| **User Service** | User profiles, Contact lists, Permission (Scope) checks, User search. | ✅ Operational |
| **Message Service** | Text and File message persistence, Chat history retrieval, Read receipts. | 🏗️ In Progress |
| **WebSocket Service** | Connection management, Real-time delivery, Presence (Online/Offline) logic. | 🏗️ In Progress |
| **File Service** | Multi-part uploads, MIME-type validation, S3 integration, Signed URLs. | 🏗️ In Progress |
| **Chat Core Service** | Group and Channel metadata, Membership management, Role-based access. | 🏗️ In Progress |
| **Notification Service** | Background events processing, Push notification routing (FCM integration). | 🏗️ In Progress |

---

## Security & Permissions
Access to resources is managed via **JWT Scopes**. Current implemented scopes include:
- `user.profile.view`: Access to own profile data.
- `user.profile.edit`: Modify own metadata (display name, bio, status).
- `user.profile.upload_avatar`: Permission to interact with the File Service for profile pictures.
- `user.profile.search_users`: Querying the user database.
- `user.profile.view_any`: Accessing public profile data of other users.
- `user.contacts.manage`: Ability to add, remove, or block contacts.
