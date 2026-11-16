# MAESTRO Pages redirects

This organization-level GitHub Pages site serves previously published links.
The [MAESTRO website](https://airi-maestro.github.io/maestro-page/) and
[documentation](https://airi-maestro.github.io/maestro-docs/ru/) deploy from
their own project repositories.

- `/care-page/` redirects browsers to `/maestro-page/`.
- `/care-docs/` and paths in the documentation sitemap redirect browsers
  to the corresponding pages under `/maestro-docs/`. The redirects retain
  query parameters and fragments. An old route outside the sitemap uses
  the site's fallback page to forward the same path.
- `/care-docs/maestro.skill` serves the same archive bytes as the current
  documentation site at build time. Download clients can use the old URL
  directly.

After a new skill archive is published, run **Actions → Publish MAESTRO
redirects → Run workflow** to refresh the compatibility copy. The workflow
reads the published docs sitemap and archive and only deploys after both
are validated.
