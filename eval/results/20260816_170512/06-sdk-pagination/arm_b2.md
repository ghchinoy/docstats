# Handling Infinite Pagination in Developer SDKs

Consuming paginated API endpoints in developer SDKs forces client developers to manage cursor tokens. This boilerplate code degrades the developer experience.

We designed our SDK client interfaces to expose asynchronous generators that handle page boundaries. Developers prefer a simple loop over complex callback handlers. The iterator manages token refresh and fetches subsequent pages on demand while keeping memory overhead bounded. This design yields cleaner client code and eliminates manual token wrangling.