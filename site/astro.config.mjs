// @ts-check
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

// https://astro.build/config
export default defineConfig({
  // GitHub Pages project site: https://ghchinoy.github.io/docstats/
  site: "https://ghchinoy.github.io",
  base: "/docstats",
  integrations: [
    starlight({
      title: "docstats",
      description:
        "Readability scoring and deterministic house-style linting for text, web pages, and PDFs. An MCP server and REST service designed as a post-hoc acceptance gate.",
      social: {
        github: "https://github.com/ghchinoy/docstats",
      },
      editLink: {
        baseUrl: "https://github.com/ghchinoy/docstats/edit/main/site/",
      },
      lastUpdated: true,
      sidebar: [
        {
          label: "Start Here",
          items: [
            { label: "What is docstats?", slug: "guides/what-is-docstats" },
            { label: "Getting Started", slug: "guides/getting-started" },
            { label: "Interpreting Scores", slug: "guides/interpreting-scores" },
          ],
        },
        {
          label: "Guides",
          items: [
            { label: "Server Modes", slug: "guides/server-modes" },
            { label: "Inputs & Extraction", slug: "guides/inputs-and-extraction" },
            { label: "CI Quality Gate", slug: "guides/ci-quality-gate" },
            { label: "Troubleshooting", slug: "guides/troubleshooting" },
          ],
        },
        {
          label: "Integrations",
          items: [
            { label: "MCP & Agent Plugins", slug: "integrations/mcp" },
            { label: "Skills", slug: "integrations/skills" },
            { label: "REST API", slug: "integrations/rest-api" },
          ],
        },
        {
          label: "Deep Dives",
          items: [
            { label: "Readability Formulas", slug: "deep-dives/readability-formulas" },
            { label: "House-Style Linting", slug: "deep-dives/house-style-linting" },
            { label: "The Two-Axis Model", slug: "deep-dives/two-axis-model" },
            {
              label: "Statistics & Evaluation",
              slug: "deep-dives/statistics-and-evaluation",
            },
            { label: "Research Program", slug: "deep-dives/research-program" },
          ],
        },
      ],
    }),
  ],
});
