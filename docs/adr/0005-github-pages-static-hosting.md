# Static dashboard on GitHub Pages

The dashboard is a static Vite build deployed by GitHub Actions to Pages, with all analysis
committed as JSON under `data/snapshots/`. There is no server, no database, and no hosting bill,
and the published numbers are byte-identical to what the pipeline produced. A project page means
`base: '/hn-agentic-ai-survey/'` is mandatory; the repo must stay public for free Pages.
