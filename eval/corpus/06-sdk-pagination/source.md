# Handling Infinite Pagination in Developer SDKs

Here's the thing: building developer SDKs that consume paginated API endpoints is fundamentally harder than it looks. It's worth noting that client developers genuinely hate managing cursor tokens manually — because boilerplate code quietly degrades developer experience — and that matters deeply.

In modern API development, pagination isn't documentation, it's ergonomics. Not `fetch_page`, just `auto_paginate`. When designing SDK client interfaces, we explicitly decided to expose asynchronous generators that automatically handle page boundaries behind the scenes.

Here's what we found: developers actually prefer a simple loop over complex callback handlers. The iterator handles token refresh transparently — fetching subsequent pages on demand — while keeping memory overhead strictly bounded.

The payoff: cleaner client code and zero manual token wrangling. Simple as that.
