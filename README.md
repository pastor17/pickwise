# PickWise — Independent Product Reviews & Buyer's Guides

> An English-language, SEO-first product review site built for overseas buyers. Launch vertical: **air purifiers**. Multi-category architecture reserved and ready to expand.

Built with [Hugo](https://gohugo.io) (static, fast, deployable to GitHub Pages). Styled after the trust-first design language of Wirecutter / RTINGS: clean editorial layout, pros & cons, comparison tables, star ratings, affiliate disclosure, and full Schema.org structured data for Google rich results.

---

## Quick start

Prerequisites: Hugo **Extended** v0.150+.

```bash
# dev server (hot reload)
hugo server -D
# → http://localhost:1313/

# production build
hugo --minify   # output → public/
```

The project ships with Hugo v0.150.0 Extended pre-installed under `.tools/hugo` in the workspace root.

---

## Site architecture

```
pickwise/
├── hugo.toml                  # config: brand, taxonomies, permalinks, affiliate tag
├── archetypes/                # `hugo new` templates (review / roundup / guide)
├── content/
│   ├── _index.md              # home
│   ├── reviews/               # single-product deep reviews   → /reviews/:slug/
│   ├── roundups/              # "Best X of 2025" lists        → /best/:slug/
│   ├── guides/                # buyer's guides                → /guides/:slug/
│   └── *.md                   # static pages (about, disclosure, etc.)
├── data/categories.yaml       # category metadata (slug, emoji, color, status)
├── layouts/                   # baseof, head/header/footer, section list+single, taxonomy
│   └── partials/
│       ├── schema/            # JSON-LD: Organization, Review, ItemList, Article, FAQPage
│       ├── cover.html         # image + emoji/gradient fallback (no layout shift)
│       ├── review-card / roundup-card / guide-card / pick-card / ...
├── assets/css/main.css        # full design system
├── assets/js/main.js          # nav, reading progress, FAQ accordion
├── static/                    # favicon.svg, robots.txt
├── scripts/amazon_images.py   # fetch official Amazon product images (PA-API 5.0)
└── .github/workflows/hugo.yml # GitHub Pages deploy
```

### Content types

| Type | Section | URL | Purpose |
|------|---------|-----|---------|
| Review | `reviews/` | `/reviews/:slug/` | Single-product deep dive: pros/cons, specs, verdict, "who should buy/skip" |
| Roundup | `roundups/` | `/best/:slug/` | Ranked "Best … of 2025" list with comparison table + pick cards |
| Guide | `guides/` | `/guides/:slug/` | Buyer's guide: key points, FAQ, how-to |

### Taxonomy

- `categories` — product categories (metadata in `data/categories.yaml`)
- `tags` — free-form (e.g. `budget`, `allergies`, `HEPA`)

Categories marked `status: "soon"` render as "coming soon" cards — the multi-category architecture is ready; content can be added later with zero code changes.

---

## Adding content

```bash
hugo new content reviews/my-product.md
hugo new content roundups/best-something-2025.md
hugo new content guides/something-guide.md
```

Fill the front matter (see archetypes for the full field reference), set `draft: false`, and write the body. The layouts render everything else automatically — comparison tables, pros/cons, star ratings, verdict boxes, FAQ, and JSON-LD are all driven by front matter.

Key front-matter fields:

- **Review** — `brand`, `product`, `rating` (0–5), `price`, `bestFor`, `pros`, `cons`, `specs` (ordered `label`/`value` list), `verdict`, `asin`.
- **Roundup** — `picks` (ordered list of `rank/brand/name/price/rating/bestFor/blurb/pros/cons/asin`), `faq`.
- **Guide** — `keyPoints`, `faq`.

---

## Affiliate setup (Amazon Associates)

1. **Set your tag** in `hugo.toml` → `[params] affiliateTag` (replace `pickwise-20`).
2. **Add ASINs** to each product's `asin:` field (front matter). Links are built automatically as `https://www.amazon.com/dp/<ASIN>?tag=<tag>` with `rel="nofollow sponsored"`.
3. The "Check price" buttons appear automatically once an `asin` is present.

> **Important:** the seed content ships with empty `asin:` values on purpose. Verify the correct ASIN for your exact product variant before going live — a wrong ASIN links to the wrong product.

---

## Images (watermark-free, legal)

We never publish watermarked images and we do **not** remove watermarks (that strips attribution and circumvents copyright — a legal risk and against our editorial policy). Instead we source images that are already watermark-free:

1. **Amazon Product Advertising API** — the official, Associates-approved source for product shots.
   ```bash
   export AMAZON_ACCESS_KEY=... AMAZON_SECRET_KEY=... AMAZON_PARTNER_TAG=yourtag-20
   python3 scripts/amazon_images.py --asins B07XXX,B08YYY --out images.yaml
   ```
2. **Manufacturer press/spec pages** — official product photography.
3. **Unsplash & royalty-free libraries** — lifestyle imagery.

Every cover supports an image URL *or* a local `assets/` path, and falls back to a clean emoji + brand-color gradient if no image is set (so there's never a broken `<img>` or layout shift).

---

## SEO & structured data

- **Per-page meta** — title, description, canonical, Open Graph, Twitter cards.
- **JSON-LD** (validated) — `Organization` + `WebSite` site-wide; then per type:
  - Reviews → `Product` + `Review` (rating, pros/cons, price/offers)
  - Roundups → `ItemList` + `FAQPage`
  - Guides → `Article` + `FAQPage`
- **Clean URLs** — `/reviews/:slug/`, `/best/:slug/`, `/guides/:slug/`.
- **`robots.txt`** and a sitemap are generated by Hugo (`enableRobotsTXT = true`).

---

## Content strategy (re-architecting Chinese-site topics for Western buyers)

Chinese review sites (什么值得买/SMZDM, 知乎, 小红书) surface strong *use-case* angles. Map them to Western search intent like this:

| Chinese angle | Western framing |
|---------------|-----------------|
| 小户型 / 租房 picks | "Best for small apartments & dorms" |
| 宠物毛 / 异味 | "Best for pet owners (dander + odor)" |
| 新房除甲醛 (VOC) | "Best for new construction & off-gassing" |
| 母婴 / 新生儿 | "Safest for nurseries (quiet + ozone-free)" |
| 性价比 / 耗材成本 | "True cost of ownership" |
| 颜值 / 智能联动 | "Best-looking + smart picks" |

The launch vertical already demonstrates this: the general list plus a **scenario list** (`best-air-purifiers-small-apartments`) and a **sizing guide** that answers the exact questions Western buyers type into Google.

---

## Deployment (GitHub Pages)

1. Set your real domain in `hugo.toml` → `baseURL`.
2. Push to a repo's `main` branch.
3. In repo **Settings → Pages → Source**, choose **GitHub Actions**.
4. `.github/workflows/hugo.yml` builds and deploys automatically on push.

---

## Customization

- **Brand & colors** — `hugo.toml` (`title`, `tagline`, `logoEmoji`) and the CSS custom properties at the top of `assets/css/main.css` (`--primary`, `--accent`, fonts, radii).
- **Categories** — `data/categories.yaml`.
- **Favicon** — `static/favicon.svg`.

---

© 2025 PickWise. All rights reserved.
