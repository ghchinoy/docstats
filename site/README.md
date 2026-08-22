# docstats documentation site

The docstats documentation site, built with [Astro](https://astro.build/) and
[Starlight](https://starlight.astro.build/). It is published to GitHub Pages at
<https://ghchinoy.github.io/docstats/>.

## Local development

```bash
cd site
npm install
npm run dev
```

The dev server runs at `http://localhost:4321/docstats/`.

## Build

```bash
npm run build      # outputs to site/dist/
npm run preview    # serve the production build locally
```

## Structure

```
site/
├── astro.config.mjs          # Starlight config, sidebar, site/base for Pages
├── src/
│   ├── content.config.ts     # docs collection loader
│   └── content/docs/
│       ├── index.mdx         # splash landing page
│       ├── guides/           # user-first explainer + how-tos
│       ├── integrations/     # MCP, skills, REST API
│       └── deep-dives/       # linguistics + statistics
└── package.json
```

Source-of-truth material lives in the repo's top-level `docs/` and `skills/`
directories; these Starlight pages adapt and structure that content for a
user-facing site. When facts change (bands, thresholds, golden-set values),
update both.

## Deployment

Pushing to `main` with changes under `site/**` triggers
`.github/workflows/deploy-docs.yml`, which builds the site and publishes it to
GitHub Pages.

### One-time repo setting

GitHub Pages must be set to build from Actions:

1. Repo **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.

After that, every qualifying push deploys automatically.
