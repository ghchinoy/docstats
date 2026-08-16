# Handling Infinite Pagination in Developer SDKs

Building developer SDKs that consume paginated API endpoints is often more challenging than it appears. Requiring developers to manage cursor tokens manually introduces repetitive boilerplate, which degrades the developer experience.

In modern SDK design, pagination is primarily a matter of ergonomics. Rather than exposing low-level methods like `fetch_page`, SDK interfaces can provide intuitive abstractions like `auto_paginate`. By leveraging asynchronous generators, client libraries can handle page boundaries seamlessly behind the scenes.

A standard iteration loop is consistently preferred over complex callback handlers. An async iterator fetches subsequent pages on demand, transparently managing token updates while keeping memory overhead strictly bounded.

The result is cleaner client code, predictable resource consumption, and zero manual token management.