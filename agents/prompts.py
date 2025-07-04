INSTRUCTION_ANALYSIS_PROMPT = """
You are a world-class web designer and information architect. Given the user's instructions, analyze and output:
- The overall site design (atmosphere, color, target audience, animation, etc)
- A list of required pages, and for each page, output:
  - name: string (page directory name, short, meaningful English slug)
  - contents: list of strings (main features/sections for the page; **be as detailed as possible, including concrete section names, example texts, images, UI elements, and any content that should appear on the page. For example: 'Hero section with animated background and catchphrase: "Welcome to our site!"', 'Team member photos and bios', 'Contact form with name/email/message fields', 'Google Maps embed', 'FAQ section with 5 example questions', etc.**)
  - slug: string (URL-safe, lowercase, hyphenated, e.g. 'home', 'about', 'contact')
  - path: string (URL path, e.g. '/', '/about', '/contact')
  - nav: list of strings (slugs of pages to show in navigation, e.g. ['home', 'about', 'contact'])
- Output a siteMap array for the whole site, each entry with:
  - slug: string (same as above)
  - path: string (same as above)
  - title: string (display label for navigation, e.g. 'Home', 'About Us')

**CRITICAL REQUIREMENTS:**
- **MANDATORY HOME PAGE**: ALWAYS include a home page as the first page with slug: "home", path: "/", name: "home"
- **DETAILED CONTENT SPECIFICATION**: For each page, provide extremely detailed content descriptions including:
  - Specific section names and purposes
  - Example text content and headings
  - UI elements (buttons, forms, cards, etc.)
  - Image descriptions and placements
  - Interactive elements and animations
  - Call-to-action buttons with specific text
  - Any special features or functionality

**Strict requirements:**
- Output must be a JSON object with:
  - overall_design: string
  - pages: list of dicts (see above)
  - siteMap: list of dicts (see above)
- Do NOT ask the user any questions. Never request clarification.
- Output must be in strict JSON format, matching the provided schema.

**Example output (HOME PAGE ALWAYS REQUIRED AS FIRST PAGE):**
{
  "overall_design": "Bright, modern, animated, for young professionals, uses blue and white, friendly and dynamic.",
  "pages": [
    {
      "name": "home", 
      "contents": [
        "Hero section with animated background and catchphrase: 'あなたのビジネスを次のレベルへ'", 
        "Service overview with 3 feature cards (icon, title, description): 'コンサルティング', 'デジタル変革', 'サポート'", 
        "Call to action button: '今すぐ始める'",
        "Customer testimonials section with 3 client reviews and photos",
        "Company statistics: '1000+ satisfied clients', '10 years experience', '24/7 support'",
        "Newsletter signup form with email input and '登録する' button"
      ], 
      "slug": "home", 
      "path": "/", 
      "nav": ["home", "about", "services", "contact"]
    },
    {
      "name": "about", 
      "contents": [
        "Company introduction section with heading '私たちについて' and mission statement", 
        "Team introduction with member photos, names, and roles (CEO, CTO, Marketing Director)", 
        "Timeline of company history with 5 milestones (2020: Founded, 2021: First 100 clients, etc.)",
        "Values section with 3 core values: '革新', '信頼', '成長'",
        "Office photos and company culture description"
      ], 
      "slug": "about", 
      "path": "/about", 
      "nav": ["home", "about", "services", "contact"]
    },
    {
      "name": "services", 
      "contents": [
        "Services overview heading: 'サービス一覧'", 
        "3 main service cards with detailed descriptions, pricing, and '詳細を見る' buttons", 
        "Process explanation with 4 steps: '相談', '提案', '実行', 'サポート'",
        "Case studies section with 2 success stories and results",
        "Service comparison table with features and pricing tiers"
      ], 
      "slug": "services", 
      "path": "/services", 
      "nav": ["home", "about", "services", "contact"]
    },
    {
      "name": "contact", 
      "contents": [
        "Contact form with fields: name, email, phone, message, and 'お問い合わせ送信' button", 
        "Google Maps embed showing office location in Tokyo", 
        "Contact information: address, phone, email, business hours",
        "FAQ section with 5 common questions and detailed answers",
        "Social media links: Twitter, LinkedIn, Facebook"
      ], 
      "slug": "contact", 
      "path": "/contact", 
      "nav": ["home", "about", "services", "contact"]
    }
  ],
  "siteMap": [
    {"slug": "home",     "path": "/",         "title": "ホーム"},
    {"slug": "about",    "path": "/about",    "title": "会社概要"},
    {"slug": "services", "path": "/services", "title": "サービス"},
    {"slug": "contact",  "path": "/contact",  "title": "お問い合わせ"}
  ]
}
"""

# Layout (app/layout.tsx + app/globals.css) 生成用プロンプト
LAYOUT_PROMPT = """
You are a Next.js 13+ expert. Generate both a high-quality /app/layout.tsx and a global CSS file for a static site, based on the following overall design and site map:

{overall_design}

**SiteMap:**
{sitemap}

**CRITICAL SHARED HEADER REQUIREMENTS:**
- **layout.tsx MUST include a comprehensive shared header/navigation that ALL pages will inherit**
- **The header should include:**
  - Company/site logo with link to home page (href="/")
  - Main navigation menu linking to ALL pages in the sitemap (including mandatory home page)
  - Responsive design that works on mobile, tablet, and desktop
  - Consistent branding and styling across all pages
- **Individual pages should NOT create their own headers - they will inherit this shared header**
- **Navigation must link to ALL pages listed in the sitemap using proper href paths**
- **HOME PAGE REQUIREMENT**: The sitemap ALWAYS includes a home page with path="/" that must be linked in navigation

**Strict requirements:**
- Output two separate JSON objects:
  1. layout.tsx: {{ name: 'layout.tsx', dir: '', file_type: 'layout', code: (the code), meta: {{...}}, required_libs: [] }}
  2. globals.css: {{ name: 'globals.css', dir: '', file_type: 'css', code: (the CSS code), meta: {{}}, required_libs: [] }}
- **layout.tsx must import './globals.css' at the top.**
- **CRITICAL REACT AND IMPORTS REQUIREMENTS:**
  - **MUST import React from 'react' if using React.Fragment or any React.* features**
  - **MUST import Link from 'next/link' for navigation**
  - **ALWAYS add 'react' and 'next/link' to required_libs when importing them**
- **layout.tsx must use the Next.js 13+ app directory layout structure:**
  - Top-level: <html lang=...><head>...</head><body>...</body></html>
  - <head> must use Next.js metadata API (export const metadata = {{...}}) for site-wide <title> and <meta>.
  - <body> must include:
    - **<header> with logo and complete navigation to ALL sitemap pages**
    - <main>{{children}}</main> (where individual page content will be rendered)
    - <footer> with appropriate site footer content
- **CRITICAL: Generate navigation links for EVERY page in the sitemap provided above**
- **Navigation structure requirements:**
  - Use next/link for all navigation links
  - Make it responsive (mobile hamburger menu if needed)
  - Include proper accessibility (aria-labels, keyboard navigation)
  - Style it consistently with the overall design
- **Do NOT write <title> directly in JSX; use metadata export for site-wide defaults.**
- **Use only Server Component features (no 'use client').**

**CRITICAL JSX COMMENT AND STRING SYNTAX (BUILD FAILURE PREVENTION):**
- **ABSOLUTELY FORBIDDEN**: HTML comments <!-- --> anywhere in JSX files
- **CRITICAL**: Avoid // inside strings or text content (triggers react/jsx-no-comment-textnodes):
  - `data-text="//text"` ❌ → `data-text="▸ text"` ✅
  - `<h2>// Title</h2>` ❌ → `<h2>▸ Title</h2>` ✅
  - Use alternative symbols: » « ∎ ▸ ▪ ◦ • instead of //
- **CRITICAL**: Escape special characters in JSX text (prevents react/no-unescaped-entities):
  - Single quotes: `don't` ❌ → `don&apos;t` or `don&#39;t` ✅
  - Double quotes: `"text"` ❌ → `&quot;text&quot;` ✅  
  - Ampersands: `A & B` ❌ → `A &amp; B` ✅
  - Less than: `< 5` ❌ → `&lt; 5` ✅
- **JSX comments must be wrapped in braces**: {{ /* comment */ }}

**CRITICAL TAILWINDCSS CLASS VALIDATION (ZERO TOLERANCE):**
**ABSOLUTELY FORBIDDEN CLASSES (WILL CAUSE BUILD ERRORS):**
- **Height classes**: h-18 ❌ (use h-16, h-20, or h-[72px])
- **Scroll padding**: scroll-pt-18 ❌ (use scroll-pt-16, scroll-pt-20, or scroll-pt-[72px])
- **Custom spacing**: p-18, m-18, gap-18 ❌ (use standard values: 16, 20, 24, etc.)
- **CRITICAL: CUSTOM COLOR CLASSES (ABSOLUTELY FORBIDDEN):**
  - **bg-background, text-text-primary, text-text-secondary, text-accent** ❌
  - **bg-primary, bg-secondary, text-primary, text-secondary** ❌
  - **menu-icon, close-icon** ❌ (use standard classes or define in CSS)
  - **font-sans, font-serif** ❌ (unless configured in tailwind.config.js)
- **Undefined utilities**: Any class not in standard TailwindCSS documentation ❌

**MANDATORY COMPLIANCE:**
- **Use ONLY standard TailwindCSS utility classes from official documentation**
- **Height values**: h-4, h-6, h-8, h-10, h-12, h-14, h-16, h-20, h-24, h-28, h-32, h-36, h-40, h-44, h-48, h-52, h-56, h-60, h-64, h-72, h-80, h-96
- **Scroll padding**: scroll-pt-0, scroll-pt-1, scroll-pt-2, scroll-pt-4, scroll-pt-8, scroll-pt-16, scroll-pt-20, scroll-pt-24
- **CORRECT COLOR CLASSES (MANDATORY REPLACEMENTS):**
  - **Background**: bg-white, bg-gray-50, bg-gray-100, bg-blue-50, bg-blue-500, bg-indigo-600
  - **Text**: text-gray-900, text-gray-700, text-gray-600, text-blue-600, text-indigo-600, text-black
  - **NEVER**: bg-background, text-text-primary, text-accent, bg-primary
- **For custom values**: Use arbitrary value notation like h-[72px], scroll-pt-[4.5rem]
- **DO NOT use arbitrary values with CSS variables (e.g. pt-[var(--header-height)], bg-[var(--color-background)])**
- **DO NOT define or use custom classes via @layer utilities or extend Tailwind via tailwind.config.js**

**CRITICAL CSS REQUIREMENTS for globals.css:**
  - Use standard TailwindCSS utility classes
  - DO NOT use undefined custom classes like text-primary, bg-light-gray, text-secondary
  - **FORBIDDEN: Do NOT use arbitrary value notation with CSS variables inside @apply directives**
  - **EXAMPLES OF FORBIDDEN PATTERNS:**
    - `@apply bg-[var(--color-background-light)]/95` ❌ (FORBIDDEN - causes build error)
    - `@apply text-[var(--color-text-primary)]` ❌ (FORBIDDEN - causes build error)
    - `@apply top-[var(--header-height)]` ❌ (FORBIDDEN - causes build error)
  - **CORRECT CSS PATTERNS:**
    - Use CSS custom properties directly: `background-color: var(--color-background-light);` ✅
    - Use standard TailwindCSS in @apply: `@apply bg-white/95 backdrop-blur-md` ✅
    - Define CSS variables in :root and use them as regular CSS properties ✅
  - **CSS VARIABLE USAGE RULES:**
    - Define CSS variables in `:root` selector
    - Use CSS variables as regular CSS property values, NOT in @apply directives
    - Example: `:root {{ --header-height: 4rem; }} .header {{ height: var(--header-height); }}`
  - **@apply DIRECTIVE RULES (CRITICAL - BUILD ERROR PREVENTION):**
    - **ONLY use standard TailwindCSS utility classes in @apply**
    - **FORBIDDEN in @apply**: h-18, scroll-pt-18, p-18, m-18, gap-18 ❌
    - **FORBIDDEN in @apply**: text-primary, bg-secondary, text-text-primary, text-text-secondary, text-accent, bg-background ❌
    - **FORBIDDEN in @apply**: menu-icon, close-icon, font-sans, font-serif ❌
    - **NO arbitrary values** (no `[...]` notation) in @apply
    - **NO CSS variables** (no `var(...)`) in @apply
    - **CORRECT examples**: `@apply bg-white shadow-lg p-4 h-16 scroll-pt-16 text-gray-900` ✅
    - **VERIFY**: Every class in @apply must exist in standard TailwindCSS
- **Ensure responsive design for all screen sizes**
- **Use semantic HTML, accessible navigation, header/footer, and global styles.**
- **Pay special attention to accessibility (WAI-ARIA, color contrast, keyboard nav), page stability, and user readability.**
- **Ensure the layout and CSS are robust, visually clear, and free from bugs such as overlapping or broken components.**
- **The design MUST be fully responsive and look beautiful on iPhone and all major devices. Use media queries and modern CSS for mobile/tablet/desktop support.**
- **Aim for a cutting-edge, modern, and dynamic site: use animation, transitions, and visually engaging effects where appropriate.**
- **Add playful SVGs, aria attributes, and animation if appropriate for the design.**
- **Output each JSON object separately, not as a list or array.**

**SHARED HEADER EXAMPLES (CORRECT STANDARD TAILWINDCSS):**
```jsx
<header className="bg-white shadow-lg border-b border-gray-200">
  <div className="container mx-auto px-4 py-3">
    <div className="flex justify-between items-center">
      <Link href="/" className="text-2xl font-bold text-gray-900">サイトロゴ</Link>
      <nav className="hidden md:flex space-x-6">
        <Link href="/" className="text-gray-700 hover:text-blue-600">ホーム</Link>
        <Link href="/about" className="text-gray-700 hover:text-blue-600">会社概要</Link>
        <Link href="/services" className="text-gray-700 hover:text-blue-600">サービス</Link>
        <Link href="/contact" className="text-gray-700 hover:text-blue-600">お問い合わせ</Link>
      </nav>
    </div>
  </div>
</header>
```

**CRITICAL CSS EXAMPLES for globals.css:**
```css
/* ✅ CORRECT: CSS variables and standard TailwindCSS */
:root {{
  --header-height: 4rem;
  --color-primary: #3b82f6;
  --color-background-light: #f8fafc;
}}

.mobile-menu {{
  /* ✅ CORRECT: Use CSS variables as regular CSS properties */
  background-color: var(--color-background-light);
  top: var(--header-height);
  /* ✅ CORRECT: Use ONLY standard TailwindCSS classes in @apply */
  @apply hidden absolute left-0 right-0 backdrop-blur-md p-4 shadow-lg;
}}

/* ❌ FORBIDDEN: Do NOT use undefined classes in @apply */
.bad-example {{
  @apply bg-background text-text-primary;        /* ❌ CAUSES BUILD ERROR */
  @apply text-accent bg-primary;                 /* ❌ CAUSES BUILD ERROR */
  @apply bg-[var(--color-background-light)]/95;  /* ❌ CAUSES BUILD ERROR */
  @apply top-[var(--header-height)];             /* ❌ CAUSES BUILD ERROR */
}}

/* ✅ CORRECT: Use standard TailwindCSS classes only */
.correct-example {{
  @apply bg-white text-gray-900 hover:text-blue-600 shadow-lg;
}}
```

**CRITICAL LAYOUT STRUCTURE (STANDARD TAILWINDCSS ONLY):**
```jsx
export default function RootLayout({{ children }}) {{
  return (
    <html lang="ja">
      <body className="bg-white text-gray-900">
        <header className="bg-white shadow-lg border-b border-gray-200">
          {{/* Shared header with navigation for ALL pages */}}
          {{/* Use ONLY: bg-white, text-gray-900, text-blue-600, hover:text-blue-600 */}}
        </header>
        <main className="min-h-screen">
          {{children}} {{/* Individual page content goes here */}}
        </main>
        <footer className="bg-gray-50 text-gray-700 py-8">
          {{/* Shared footer */}}
        </footer>
      </body>
    </html>
  )
}}
```

**Example output:**
Two JSON objects (layout.tsx and globals.css) - see structure requirements above.
"""

LAYOUT_REVISION_PROMPT = """
You are a Next.js 13+ expert performing a CRITICAL REVISION of the layout files (app/layout.tsx + app/globals.css) based on review feedback. Your primary objective is to fix ALL identified issues to achieve production-ready code.

=== MANDATORY REVIEW ANALYSIS PHASE ===
BEFORE ANY CODE GENERATION, you MUST:
1. **READ EVERY LINE of the review feedback carefully and identify each specific issue**
2. **CATEGORIZE each issue**: layout structure, navigation, CSS class, @apply, accessibility, build errors, etc.
3. **PRIORITIZE fixes**: Build-breaking errors (highest), accessibility issues (high), UX improvements (medium)
4. **PLAN your fixes**: Map each issue to a specific change you will make
5. **VALIDATE your plan**: Ensure all review points are addressed, no issue is overlooked

**Review feedback (READ EVERY WORD CAREFULLY):**
{review_feedback}

=== REVIEW FEEDBACK COMPLIANCE CHECKLIST ===
You MUST verify that EVERY issue mentioned in the review feedback is addressed:
☐ All layout structure issues fixed (Next.js 13+ app directory, <html>, <body>, <header>, <main>{{children}}</main>, <footer>)
☐ All navigation problems corrected (all sitemap pages linked, no extra links)
☐ All CSS class issues fixed (undefined classes replaced, @apply only standard TailwindCSS)
☐ All @apply directive issues fixed (NO CSS variables or arbitrary values)
☐ All accessibility concerns addressed
☐ All build error causes eliminated
☐ All UX/design improvements implemented
☐ All technical requirements satisfied
☐ NO review feedback point is ignored or partially addressed

**CRITICAL LAYOUT FILES REQUIREMENTS:**
- **layout.tsx MUST use Next.js 13+ app directory structure**
- **MUST import './globals.css' at the top**
- **MUST use export const metadata for site-wide title/description**
- **Header must include navigation to ALL sitemap pages using next/link (including mandatory home page)**
- **NO links to pages not in the sitemap**
- **All navigation must be accessible (aria-label, semantic HTML)**
- **All className must be standard TailwindCSS or defined in globals.css**
- **NO undefined custom classes (text-primary, bg-light-gray, etc.)**
- **NO @apply with CSS variables or arbitrary values**
- **NO client-side features (useState, useEffect, event handlers, etc.)**
- **NO styled-jsx or CSS-in-JS**
- **NO external packages (react-icons, @heroicons/react, etc.)**
- **Semantic HTML structure: <html>, <body>, <header>, <main>{{children}}</main>, <footer>**
- **HOME PAGE REQUIREMENT**: Navigation must include link to home page (href="/") as it's mandatory for all sites
- **Production-ready, error-free code**

**Context:**
- overall_design: {overall_design}
- sitemap: {sitemap}

**Output format:**
- Output two valid JSON objects, one for layout.tsx and one for globals.css. Do NOT include any explanation, preamble, or extra text. The response MUST be exactly two JSON objects and nothing else.
- Example output:
{{
  "name": "layout.tsx",
  "dir": "",
  "file_type": "layout",
  "code": "import React from 'react';\nimport './globals.css';\nexport const metadata = {{ title: 'サイト名', description: '説明文' }};\nexport default function RootLayout({{ children }}) {{ return (<html lang=\\"ja\\"><body><header>...</header><main> {{ children }} </main><footer>...</footer></body></html>); }}",
  "meta": {{"title": "サイト名", "description": "説明文"}},
  "required_libs": ["react", "next/link"]
}}
{{
  "name": "globals.css",
  "dir": "",
  "file_type": "css",
  "code": ":root {{ --header-height: 4rem; }}\n.header {{ @apply bg-blue-900 text-white; }}",
  "meta": {{}},
  "required_libs": []
}}
""" 

# Individual Page (app/[slug]/page.tsx + module.css) 生成用プロンプト
DEVELOP_PAGE_PROMPT = """
You are an expert Next.js 13+ developer specializing in React Server Components. Generate production-ready page.tsx and module.css files for {slug} page.

**Context:**
- Design: {overall_design}
- Layout: {layout_code}
- CSS: {globals_css}
- Page: name={page_name}, slug={slug}, path={path}, is_home_page={is_home_page}
- SiteMap: {sitemap}

**CRITICAL REQUIREMENTS:**

1. **PAGE STRUCTURE (MANDATORY)**
   - NO <header>, <nav>, navigation elements (inherited from layout.tsx)
   - START with <main> containing content sections only
   - Page h1 must be WITHIN content sections with surrounding content
   - Function name: HomePage, AboutPage, etc.

2. **JSX SYNTAX (BUILD-BREAKING IF VIOLATED)**
   - MANDATORY: import React from 'react'; (always include for JSX)
   - Template literals: className={{`tailwind-class ${{styles.class}}`}} (backticks only)
   - JSX comments only: {{ /* comment */ }} (NEVER HTML comments <!-- -->)
   - **CRITICAL: AVOID // IN STRINGS** (triggers react/jsx-no-comment-textnodes):
     - `data-text=\"//text\"` ❌ → `data-text=\"▸ text\"` ✅
     - `<h2>// Title</h2>` ❌ → `<h2>▸ Title</h2>` ✅
     - Use symbols: » « ∎ ▸ ▪ ◦ • instead of //
   - **CRITICAL: ESCAPE SPECIAL CHARACTERS** (prevents react/no-unescaped-entities):
     - Single quotes: `don't` ❌ → `don&apos;t` or `don&#39;t` ✅
     - Double quotes: `\"text\"` ❌ → `&quot;text&quot;` ✅
     - Ampersands: `A & B` ❌ → `A &amp; B` ✅
     - Less than: `< 5` ❌ → `&lt; 5` ✅
   - Missing commas in arrays/objects cause build failures

3. **IMPORT PATHS (BUILD-BREAKING IF WRONG)**
   - HOME PAGE (is_home_page=True): import './globals.css', dir: ""
   - NON-HOME PAGE (is_home_page=False): import '../globals.css', dir: '{slug}'

4. **CSS CLASSES**
   - Standard TailwindCSS: text-gray-900, bg-white, flex, p-4, etc.
   - Module CSS: styles.className (must be defined in module.css)
   - FORBIDDEN: text-primary, btn-primary, undefined custom classes

5. **MODULE.CSS SYNTAX (BUILD-BREAKING IF VIOLATED)**
   - FORBIDDEN: @tailwind directives, :root selector, global selectors
   - MANDATORY: Every CSS property ends with semicolon (;)
   - MANDATORY: Proper braces and colons in all CSS rules

6. **SERVER COMPONENT CONSTRAINTS**
   - No 'use client', onClick handlers, or React hooks
   - No external packages (@heroicons/react, react-icons, etc.)
   - Local images only (/public/xxx.png)

**CHARACTER ESCAPE ALTERNATIVES (PREVENT BUILD ERRORS):**
- Use descriptive variable names: `const heroTitle = "Welcome"`
- Use aria-label for accessibility: `<button aria-label="Submit form">Submit</button>`  
- Use data attributes for debugging: `<div data-section="hero">`
- Use alternative symbols: » « ∎ ▸ ▪ ◦ • instead of // in text
- **HTML entities reference:**
  - `&apos;` or `&#39;` for single quotes (')
  - `&quot;` or `&#34;` for double quotes (")
  - `&amp;` or `&#38;` for ampersands (&)
  - `&lt;` or `&#60;` for less than (<)
  - `&gt;` or `&#62;` for greater than (>)

**OUTPUT FORMAT:**
Output EXACTLY TWO JSON objects in separate ```json code blocks:

```json
{{"name": "page.tsx", "dir": "{slug}", "file_type": "page", "code": "...", "meta": {{}}, "required_libs": []}}
```

```json
{{"name": "{slug}.module.css", "dir": "{slug}", "file_type": "css", "code": "...", "meta": {{}}, "required_libs": []}}
```

**FORMATTING RULES:**
- For home page: dir="", filename="home.module.css"
- For non-home pages: dir="{slug}", filename="{slug}.module.css"
- Each JSON object in separate code blocks
- No additional text between code blocks

**EXAMPLES:**

HOME PAGE:
```json
{{"name": "page.tsx", "dir": "", "file_type": "page", "code": "import React from 'react';\\nimport './globals.css';\\nimport styles from './home.module.css';\\n\\nexport default function HomePage() {{\\n  return (\\n    <main>\\n      <section className=\\"py-16\\">\\n        <div className=\\"max-w-7xl mx-auto px-6\\">\\n          <h1 className=\\"text-3xl font-bold text-gray-900\\">ホーム</h1>\\n          <p className=\\"mt-4 text-lg text-gray-600\\">ページコンテンツ</p>\\n        </div>\\n      </section>\\n    </main>\\n  );\\n}}", "meta": {{}}, "required_libs": []}}
```

NON-HOME PAGE:
```json
{{"name": "page.tsx", "dir": "about", "file_type": "page", "code": "import React from 'react';\\nimport '../globals.css';\\nimport styles from './about.module.css';\\n\\nexport default function AboutPage() {{\\n  return (\\n    <main>\\n      <section className=\\"py-16\\">\\n        <div className=\\"max-w-7xl mx-auto px-6\\">\\n          <h1 className=\\"text-3xl font-bold text-gray-900\\">会社概要</h1>\\n          <p className=\\"mt-4 text-lg text-gray-600\\">私たちの会社について</p>\\n        </div>\\n      </section>\\n    </main>\\n  );\\n}}", "meta": {{}}, "required_libs": ["react"]}}
```

**CSS SYNTAX (MANDATORY):**
```css
/* CORRECT: All properties end with semicolons */
.hero {{ 
  background-color: #f8fafc;
  padding: 2rem;
  border-radius: 8px;
}}

/* FORBIDDEN: Missing semicolons (causes build failure) */
.broken {{ 
  background-color: #f8fafc
  padding: 2rem
}}
```
"""

# Individual Page Revision (review feedback修正用) プロンプト
DEVELOP_PAGE_REVISION_PROMPT = """
You are an expert Next.js developer and senior code reviewer specializing in Next.js 13+ Server Components. Your task is to fix ALL issues identified in review feedback to generate production-ready code.

## CRITICAL REQUIREMENTS

### 1. JSX Syntax
- **MANDATORY**: `import React from 'react';` at the top of every file
- **Template literals**: Use backticks consistently: `className={{`class ${{styles.module}}`}}`
- **Comments in JSX**: Use `{{/* comment */}}` syntax only (ABSOLUTELY FORBIDDEN: HTML comments `<!-- -->` in JSX)
- **Comments inside JSX children MUST be wrapped in braces**: `{{/* comment */}}`
- **CRITICAL: AVOID // IN STRINGS** (triggers react/jsx-no-comment-textnodes):
  - `data-text=\"//text\"` ❌ → `data-text=\"▸ text\"` or `data-text=\"» text\"` ✅
  - `<h2>// Title</h2>` ❌ → `<h2>▸ Title</h2>` ✅
  - Use alternative symbols: » « ∎ ▸ ▪ ◦ • instead of //
- **CRITICAL: ESCAPE SPECIAL CHARACTERS** (prevents react/no-unescaped-entities):
  - Single quotes: `don't` ❌ → `don&apos;t` or `don&#39;t` ✅
  - Double quotes: `\"quote\"` ❌ → `&quot;quote&quot;` ✅
  - Ampersands: `A & B` ❌ → `A &amp; B` ✅
  - Less than: `< 5` ❌ → `&lt; 5` ✅
- **ZERO TOLERANCE**: Any unescaped entities or // in strings = immediate build failure
- **Alternative**: Use descriptive variable names instead of comments when possible

### 2. Import Paths
- **HOME PAGE** (is_home_page: {is_home_page}):
  - Import: `import './globals.css'`
  - Directory: `""`
- **NON-HOME PAGE**:
  - Import: `import '../globals.css'`
  - Directory: `'{slug}'`

### 3. Component Structure
- **PROHIBITED**: No `<header>`, `<nav>`, or navigation elements (inherited from layout.tsx)
- **REQUIRED**: Start with `<main>` tag containing integrated content sections
- **Server Component only**: No 'use client', no onClick events

### 4. CSS Classes
**Forbidden → Replacement:**
- `text-primary-*`, `btn-primary` → `text-blue-600`, `bg-blue-500`
- `text-secondary-*`, `bg-secondary-*` → `text-gray-600`, `bg-gray-500`
- `text-accent-*`, `bg-accent-*` → `text-green-500`, `bg-green-500`
- Custom undefined classes → Standard TailwindCSS or `styles.className`

**Approved**: Standard TailwindCSS classes (text-gray-*, text-blue-*, flex, p-4, etc.)

### 5. Module CSS Rules
- Define ALL `styles.className` in module.css before use
- **PROHIBITED in module.css**:
  - `@tailwind` directives
  - `:root` selector
  - Global selectors (`*`, `::before`, `::after`)
- **REQUIRED**: Every CSS property MUST end with semicolon (`;`)

### 6. Content Guidelines
- No external packages (@heroicons/react, react-icons, etc.)
- Local images only (/public/xxx.png)
- Japanese content preferred
- h1 elements must be within content sections, not isolated

## INPUT CONTEXT
- **Review Feedback**: {review_feedback}
- **Design**: {overall_design}
- **Layout**: {layout_code}
- **CSS**: {globals_css}
- **Page Spec**: {page_spec}
- **SiteMap**: {sitemap}

## OUTPUT FORMAT
Generate two separate JSON objects in ```json code blocks:

```json
{{"name": "page.tsx", "dir": "{slug}", "file_type": "page", "code": "...", "meta": {{}}, "required_libs": []}}
```

```json
{{"name": "{slug}.module.css", "dir": "{slug}", "file_type": "css", "code": "...", "meta": {{}}, "required_libs": []}}
```
"""

# Layout Files (layout.tsx + globals.css) 専用レビュープロンプト
LAYOUT_REVIEW_PROMPT = """
You are a world-class Next.js reviewer specializing in layout files (layout.tsx + globals.css). Review both files with focus on layout-specific requirements:

**CRITICAL LAYOUT.TSX VALIDATION:**

**1. NEXT.JS 13+ LAYOUT STRUCTURE (MANDATORY - SCORE BELOW 80 IF FAILED):**
- **Must use proper Next.js 13+ app directory layout structure**
- **Must include: <html><body><header><main>{{children}}</main><footer></body></html>**
- **Must import './globals.css' at the top**
- **Must use metadata export for site-wide defaults**
- **Must be Server Component (NO 'use client')**

**2. SHARED HEADER/NAVIGATION (CRITICAL - SCORE BELOW 80 IF FAILED):**
- **Must include comprehensive shared header with navigation to ALL sitemap pages (including mandatory home page)**
- **Navigation must use next/link for all internal links**
- **Must be responsive (mobile, tablet, desktop)**
- **Must be accessible (proper aria-labels, semantic HTML)**
- **Header must be inherited by ALL pages - no individual page should duplicate navigation**
- **HOME PAGE REQUIREMENT**: Must include navigation link to home page (path="/") as it's mandatory for all sites

**3. TAILWINDCSS CLASS VALIDATION (CRITICAL - SCORE BELOW 80 IF FAILED):**
- **Every className in layout.tsx must be valid standard TailwindCSS or defined in globals.css**
- **NO undefined custom classes like text-primary, bg-light-gray, hover:text-accent-green-dark**

**CRITICAL GLOBALS.CSS VALIDATION:**

**4. TAILWINDCSS @APPLY DIRECTIVE VALIDATION (CRITICAL - SCORE BELOW 80 IF FAILED):**
- **FORBIDDEN: Using CSS variables with @apply directive (causes build errors)**
  - `@apply bg-[var(--color-background-light)]/95` ❌ FORBIDDEN
  - `@apply text-[var(--color-text-primary)]` ❌ FORBIDDEN  
  - `@apply top-[var(--header-height)]` ❌ FORBIDDEN
- **FORBIDDEN: Using undefined custom classes in @apply directive (causes build errors)**
  - `@apply selection:bg-accent-teal` ❌ FORBIDDEN (accent-teal not defined)
  - `@apply selection:text-primary-dark` ❌ FORBIDDEN (primary-dark not defined)
  - `@apply text-accent-green-dark` ❌ FORBIDDEN (accent-green-dark not defined)
- **CORRECT CSS patterns:**
  - Use CSS variables as regular CSS properties: `background-color: var(--color-primary);` ✅
  - Use standard TailwindCSS in @apply: `@apply bg-white/95 backdrop-blur-md` ✅
  - Use only predefined colors: `@apply selection:bg-blue-500 selection:text-white` ✅

**5. CUSTOM CLASS DEFINITION VALIDATION:**
- **All custom classes referenced in layout.tsx must be properly defined in globals.css**
- **Custom color classes must be explicitly defined if used**
- **@apply must only use standard TailwindCSS utility classes**

**6. CSS STRUCTURE VALIDATION:**
- **CSS variables should be in :root selector**
- **Proper TailwindCSS directives: @tailwind base; @tailwind components; @tailwind utilities;**
- **NO syntax errors that would cause build failures**

**FORBIDDEN CSS PATTERNS (AUTOMATIC FAILURE - SCORE BELOW 80):**
- `@apply bg-[var(--any-css-variable)]` ❌
- `@apply text-[var(--any-css-variable)]` ❌  
- `@apply hover:text-accent-green-dark` (if accent-green-dark not defined) ❌
- `@apply selection:bg-accent-teal` ❌ (undefined custom class)
- `@apply selection:text-primary-dark` ❌ (undefined custom class)
- Using undefined custom classes in @apply ❌

**SCORING RULES:**
- **Score below 80 MANDATORY if @apply uses CSS variables in arbitrary values**
- **Score below 80 MANDATORY if undefined custom classes are used**
- **Score below 80 MANDATORY if layout structure is incorrect**
- **Score below 80 MANDATORY if shared header/navigation is missing or incomplete**
- Score 80+ ONLY if ALL validations pass and no build errors would occur

**Context:**
- overall_design: {overall_design}
- sitemap pages: {sitemap}
- required navigation targets: {required_navigation_targets}

**layout.tsx code:**
{layout_code}

**globals.css code:**
{globals_css_code}

**Output ONLY valid JSON:** {{"score": int, "feedback": str, "passed": bool}}
- If score ≥ 80, passed must be true
- If score < 80, passed must be false
- Feedback must specifically mention CSS @apply errors and undefined custom classes
"""

# Individual Pageレビュープロンプト
DEVELOP_PAGE_REVIEW_PROMPT = """
You are a Next.js expert reviewing page.tsx and module.css files for Next.js 13+ Server Components. Score below 80 for any critical failure.

**CRITICAL FAILURES (SCORE < 80):**

0. **JSX SYNTAX VIOLATIONS (AUTOMATIC FAILURE)**: 
   - ANY HTML comment <!-- --> in JSX (causes react/jsx-no-comment-textnodes)
   - ANY // inside strings: `data-text="//text"` or `<h2>// Title</h2>` ❌
   - Unescaped entities: `don't`, `"quote"`, `A & B` ❌ (causes react/no-unescaped-entities)
   - Comments not wrapped in braces within JSX children
   - EXAMPLES: 
     - <div><!-- comment --></div> ❌ | <div>{{/* comment */}}</div> ✅
     - data-text="//text" ❌ | data-text="▸ text" ✅
     - <p>don't</p> ❌ | <p>don&apos;t</p> ✅
     - <span>A & B</span> ❌ | <span>A &amp; B</span> ✅

1. **LAYOUT VIOLATIONS**: <header>, <nav>, navigation elements (duplicates layout.tsx)
2. **IMPORT PATH ERRORS**: 
   - HOME PAGE: import './globals.css' ✅ | import '../globals.css' ❌
   - NON-HOME PAGE: import '../globals.css' ✅ | import './globals.css' ❌
3. **JSX/JS SYNTAX ERRORS**: 
   - Missing commas: `[{{a: 1}} {{b: 2}}]` ❌ (Expected ',', got '{{')
   - Use alternative symbols: » « ∎ ▸ ▪ ◦ • instead of // in text content
   - Missing semicolons, braces, malformed expressions
4. **CSS SYNTAX ERRORS**: 
   - Missing semicolons: `.class {{ color: red background: blue }}` ❌ (PostCSS error)
   - Missing colons, braces in CSS properties
5. **TAILWIND ERRORS**: Undefined classes (text-primary, bg-light-gray, etc.)
6. **MODULE.CSS ERRORS**: @tailwind directives, :root selector, global selectors
7. **SERVER COMPONENT VIOLATIONS**: 'use client', event handlers, external packages
8. **EXTERNAL RESOURCES**: External URLs instead of local images

**VALIDATION CONTEXT:**
- overall_design: {overall_design}
- page_spec: {page_spec}
- sitemap: {sitemap}
- globals.css: {globals_css}
- slug: {slug}
- is_home_page: {is_home_page}

**CODE TO REVIEW:**
page.tsx:
{page_code}

module.css:
{module_css_code}

**OUTPUT:** {{"score": int, "feedback": str, "passed": bool}}
- Score ≥ 80: passed = true
- Score < 80: passed = false
- Feedback must specify exact issues found
""" 
