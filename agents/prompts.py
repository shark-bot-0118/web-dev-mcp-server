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
You are an expert Next.js developer and frontend architect specializing in React Server Components and modern web development. Your expertise includes TypeScript, TailwindCSS, module CSS, component architecture, and creating production-ready, accessible web applications.

🚨 CRITICAL: Generate Next.js 13+ Server Component page for layout.tsx's <main>{{children}}</main>.
🚫 NO <header>, <nav>, navigation - inherited from layout.tsx automatically.
✅ START with <main> containing integrated content sections.

**Context:**
- Design: {overall_design}
- Layout: {layout_code}
- CSS: {globals_css}
- Page: name={page_name}, slug={slug}, path={path}, is_home_page={is_home_page}
- SiteMap: {sitemap}

**🚨 CRITICAL MODULE CSS REQUIREMENTS (VIOLATION = BUILD FAILURE):**
- **FORBIDDEN in module.css files:**
  - `@tailwind base;` ❌ (causes "Selector is not pure" error)
  - `@tailwind components;` ❌ (causes "Selector is not pure" error)  
  - `@tailwind utilities;` ❌ (causes "Selector is not pure" error)
  - `:root` selector ❌ (only allowed in globals.css)
  - Global selectors like `*`, `::before`, `::after` ❌
- **REQUIRED in module.css files:**
  - ✅ Only local CSS classes: `.className {{ properties }}`
  - ✅ Pure selectors with local scope
  - ✅ No global imports or directives

**🚨 CRITICAL CSS SYNTAX REQUIREMENTS (VIOLATION = BUILD FAILURE):**
- **MANDATORY SEMICOLONS:** Every CSS property MUST end with semicolon (`;`)
  - ✅ CORRECT: `.class {{ color: red; background: blue; }}`
  - ❌ FORBIDDEN: `.class {{ color: red background: blue }}` (missing semicolons)
  - ❌ FORBIDDEN: `.class {{ color: red; background: blue }}` (missing final semicolon)
- **MANDATORY PROPERTY SYNTAX:** 
  - ✅ CORRECT: `property: value;` (colon + space + semicolon)
  - ❌ FORBIDDEN: `property:value` (missing spaces/semicolon)
  - ❌ FORBIDDEN: `property value;` (missing colon)
- **MANDATORY BRACE SYNTAX:**
  - ✅ CORRECT: `.class {{ property: value; }}`
  - ❌ FORBIDDEN: `.class property: value;` (missing braces)
  - ❌ FORBIDDEN: `.class {{ property: value` (missing closing brace)
- **VALIDATION CHECKLIST for module.css:**
  - Every line with CSS property ends with semicolon
  - Every CSS rule has opening and closing braces
  - Every property has colon separator
  - No trailing commas in CSS (unlike JavaScript)
- **ZERO TOLERANCE:** Any syntax error will cause PostCSS build failure

**🚨 CRITICAL JSX REQUIREMENTS (VIOLATION = BUILD FAILURE):**

1. **REACT IMPORT & JSX SYNTAX**
   - ✅ MANDATORY: import React from 'react'; (ALWAYS include for JSX)
   - ✅ MANDATORY: Proper JSX syntax with React components
   - ✅ Function name must match purpose: HomePage, AboutPage, etc.
   - ✅ CRITICAL: Template literals must use backticks consistently: className={{`text-white ${{styles.class}}`}}
   - ❌ NO mixed quotes in template literals: className="text-white ${{styles.class}}" (CAUSES BUILD ERROR)
   - ❌ NO JSX without React import (causes build errors)

2. **PAGE STRUCTURE & HEADER AVOIDANCE**
   - 🚫 Forbidden: <header>, <nav>, site title, logo, navigation
   - 🚫 CRITICAL: NO isolated header-like sections at page start
   - ✅ Required: <main> with integrated content sections
   - ✅ PAGE TITLE: h1 WITHIN content sections with surrounding content
   - ✅ PATTERN: <main><section><div><h1>Title</h1><p>content</p></div></section></main>

3. **IMPORT PATHS (CRITICAL - CHECK is_home_page: {is_home_page})**
   - HOME PAGE: import './globals.css', dir: ""
   - NON-HOME PAGE: import '../globals.css', dir: '{slug}'

4. **CSS CLASSES & TEMPLATE LITERALS (BUILD-SAFE ONLY)**
   - ✅ Standard TailwindCSS: text-gray-*, bg-white, flex, p-4, etc.
   - ✅ Module CSS: styles.className (must be defined in module.css)
   - ✅ Template literals: className={{`tailwind-class ${{styles.moduleClass}}`}} (BACKTICKS ONLY)
   - 🚫 Forbidden: text-primary-*, btn-primary, undefined custom classes
   - 🚫 CRITICAL: Mixed quotes in template literals (causes JSX syntax errors)

**OUTPUT FORMAT:**
Output EXACTLY TWO separate JSON objects in ```json code blocks (CRITICAL FOR PARSING):

```json
{{"name": "page.tsx", "dir": "{slug}", "file_type": "page", "code": "...", "meta": {{}}, "required_libs": []}}
```

```json
{{"name": "{slug}.module.css", "dir": "{slug}", "file_type": "css", "code": "...", "meta": {{}}, "required_libs": []}}
```

**CRITICAL FORMATTING RULES:**
- Each JSON object MUST be wrapped in separate ```json code blocks
- Output exactly 2 code blocks: one for page.tsx, one for module.css
- No additional text between the code blocks
- For home page: use "home.module.css" as the CSS filename, dir should be ""
- For non-home pages: use "{slug}.module.css" as the CSS filename

**ADDITIONAL RULES:**
- Server Component only (no 'use client', no onClick events)  
- No external packages (@heroicons/react, react-icons, etc.)
- No :root in module.css
- Local images only (/public/xxx.png)
- Japanese content preferred
- Module CSS classes must be defined before use
- **CRITICAL HEADER AVOIDANCE:** Page h1 must be WITHIN content sections with surrounding content, not isolated as header-like elements
- **PAGE STRUCTURE:** Always start with content-rich sections, never with standalone title/intro sections that resemble headers

**EXAMPLE:**
HOME PAGE (is_home_page=True):
```json
{{"name": "page.tsx", "dir": "", "file_type": "page", "code": "import React from 'react';\\nimport './globals.css';\\nimport styles from './home.module.css';\\n\\nexport default function HomePage() {{\\n  return (\\n    <main>\\n      <section className=\\"py-16\\">\\n        <div className=\\"max-w-7xl mx-auto px-6\\">\\n          <h1 className=\\"text-3xl font-bold text-gray-900\\">ホーム</h1>\\n          <p className=\\"mt-4 text-lg text-gray-600\\">ページコンテンツ</p>\\n        </div>\\n      </section>\\n    </main>\\n  );\\n}}", "meta": {{}}, "required_libs": []}}
```

```json
{{"name": "home.module.css", "dir": "", "file_type": "css", "code": ".container {{ padding: 2rem; }}", "meta": {{}}, "required_libs": []}}
```

NON-HOME PAGE (is_home_page=False):  
```json
{{"name": "page.tsx", "dir": "about", "file_type": "page", "code": "import React from 'react';\\nimport '../globals.css';\\nimport styles from './about.module.css';\\n\\nexport default function AboutPage() {{\\n  return (\\n    <main>\\n      <section className=\\"py-16\\">\\n        <div className=\\"max-w-7xl mx-auto px-6\\">\\n          <h1 className=\\"text-3xl font-bold text-gray-900\\">会社概要</h1>\\n          <p className=\\"mt-4 text-lg text-gray-600\\">私たちの会社について</p>\\n        </div>\\n      </section>\\n    </main>\\n  );\\n}}", "meta": {{}}, "required_libs": ["react"]}}
```

```json
{{"name": "about.module.css", "dir": "about", "file_type": "css", "code": ".container {{ padding: 2rem; margin: 1rem; background-color: white; }}", "meta": {{}}, "required_libs": []}}
```

**🚨 CSS SYNTAX EXAMPLES (CRITICAL - PREVENT BUILD ERRORS):**
```css
/* ✅ CORRECT: All properties end with semicolons */
.hero {{ 
  background-color: #f8fafc;
  padding: 2rem; 
  margin-bottom: 1rem;
  border-radius: 8px;
}}

.button {{ 
  background: blue; 
  color: white; 
  padding: 1rem 2rem;
}}

/* ❌ FORBIDDEN: Missing semicolons (PostCSS ERROR) */
.bad-example {{ 
  background-color: #f8fafc
  padding: 2rem
  margin-bottom: 1rem
}}
```
"""

# Individual Page Revision (review feedback修正用) プロンプト
DEVELOP_PAGE_REVISION_PROMPT = """
You are an expert Next.js developer and senior code reviewer specializing in debugging, fixing production issues, and ensuring code quality. Your expertise includes identifying and resolving JSX syntax errors, CSS class conflicts, import path issues, and component architecture problems in React Server Components.

🚨 CRITICAL REVISION: Fix ALL issues in review feedback to generate perfect Next.js 13+ Server Component.
🚫 NO <header>, <nav> - inherited from layout.tsx.
✅ MANDATORY: import React from 'react'; (ALWAYS include for JSX syntax)
✅ START with <main> containing integrated content sections.

**IMPORT PATHS (CHECK is_home_page: {is_home_page})**
- HOME PAGE: import './globals.css', dir: ""
- NON-HOME PAGE: import '../globals.css', dir: '{slug}'

**REVIEW FEEDBACK TO FIX:**
{review_feedback}

**🚨 CRITICAL FIXES REQUIRED:**

1. **FIX JSX SYNTAX** - ALWAYS include import React from 'react'; at the top
   - CRITICAL: Fix template literal syntax - use backticks consistently: className={{`class ${{styles.module}}`}}
2. **FIX HEADER VIOLATIONS** - Remove ALL <header>, <nav>, navigation elements
3. **FIX CSS CLASSES** - Replace undefined classes with standard TailwindCSS
4. **FIX MODULE CSS** - Define ALL styles.className in module.css
5. **FIX IMPORTS** - Use correct globals.css path based on page location
6. **FIX STRUCTURE** - Ensure proper JSX syntax and component structure
7. **🚨 FIX CSS SYNTAX ERRORS** - MANDATORY semicolon validation
   - Every CSS property MUST end with semicolon (`;`)
   - Every CSS rule MUST have opening and closing braces
   - Check for missing colons, spaces, and proper syntax
   - ZERO TOLERANCE for PostCSS syntax errors

**CSS CLASS REPLACEMENTS:**
- ❌ text-primary-*, btn-primary → ✅ text-blue-600, bg-blue-500
- ❌ text-secondary-*, bg-secondary-* → ✅ text-gray-600, bg-gray-500  
- ❌ text-accent-*, bg-accent-* → ✅ text-green-500, bg-green-500
- ❌ Custom undefined classes → ✅ Standard TailwindCSS or styles.className
- ✅ Approved: text-gray-*, text-blue-*, flex, p-4, etc.

**CONTEXT:**
- Design: {overall_design}
- Layout: {layout_code}  
- CSS: {globals_css}
- Page Spec: {page_spec}
- SiteMap: {sitemap}

**APPLY SAME JSX REQUIREMENTS AS DEVELOP_PAGE_PROMPT:**
1. ✅ MANDATORY: import React from 'react'; (ALWAYS include for JSX)
   - ✅ CRITICAL: Template literals must use backticks: className={{`text-white ${{styles.class}}`}}
2. 🚫 NO header elements (<header>, <nav> prohibited)
3. ✅ CSS classes (standard TailwindCSS + module CSS only)
4. 🚨 Import paths (HOME: './globals.css', NON-HOME: '../globals.css')
5. 🚫 Forbidden classes (text-primary, btn-primary, custom undefined)

**OUTPUT:** Two separate JSON objects in ```json code blocks:

```json
{{"name": "page.tsx", "dir": "{slug}", "file_type": "page", "code": "...", "meta": {{}}, "required_libs": []}}
```

```json
{{"name": "{slug}.module.css", "dir": "{slug}", "file_type": "css", "code": "...", "meta": {{}}, "required_libs": []}}
```

**ADDITIONAL RULES:**
- Server Component only (no 'use client', no onClick events)  
- No external packages (@heroicons/react, react-icons, etc.)
- **🚨 CRITICAL: No @tailwind directives in module.css (causes build errors)**
- **🚨 CRITICAL: No :root selector in module.css (only allowed in globals.css)**
- **🚨 CRITICAL: No global selectors (*, ::before, ::after) in module.css**
- Local images only (/public/xxx.png)
- Japanese content preferred
- Module CSS classes must be defined before use
- **CRITICAL HEADER AVOIDANCE:** Page h1 must be WITHIN content sections with surrounding content, not isolated as header-like elements
- **PAGE STRUCTURE:** Always start with content-rich sections, never with standalone title/intro sections that resemble headers
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
You are a Next.js expert reviewing individual page files (page.tsx + module.css) for Next.js 13+ Server Components.

**CRITICAL FAILURES (AUTOMATIC SCORE < 80):**

1. **LAYOUT INHERITANCE VIOLATIONS:**
   - Including <header>, <nav>, or navigation elements (duplicates layout.tsx)
   - Must start with <main> or content sections only

2. **IMPORT PATH ERRORS (BUILD-BREAKING):**
   - is_home_page={is_home_page} determines correct path:
   - HOME PAGE (True): import './globals.css' ✅ | import '../globals.css' ❌  
   - NON-HOME PAGE (False): import '../globals.css' ✅ | import './globals.css' ❌

3. **TAILWINDCSS CLASS ERRORS:**
   - Undefined custom classes: text-primary, bg-light-gray, hover:text-accent-green-dark, etc.
   - Classes must be: standard TailwindCSS, globals.css-defined, or styles.className

4. **MODULE.CSS BUILD ERRORS:**
   - @tailwind directives: @tailwind base/components/utilities ❌ (causes "Selector is not pure")
   - Global selectors: *, ::before, ::after ❌ (causes "Selector is not pure")  
   - :root selector ❌ (only allowed in globals.css)
   - Only pure local classes allowed: .className {{ properties }}

5. **🚨 CSS SYNTAX ERRORS (CRITICAL - AUTOMATIC SCORE < 80):**
   - Missing semicolons: `.class {{ color: red background: blue }}` ❌ (PostCSS error)
   - Missing colons: `.class {{ color red; }}` ❌ (invalid syntax)
   - Missing braces: `.class color: red;` ❌ (invalid syntax)
   - Incomplete properties: `.class {{ color: }}` ❌ (empty value)
   - **ZERO TOLERANCE:** Any CSS syntax error causes build failure

6. **SERVER COMPONENT VIOLATIONS:**
   - 'use client' directive, event handlers (onClick), hooks (useState), browser APIs
   - External packages: @heroicons/react, react-icons, lucide-react, @mui/material ❌
   - Only allowed: React, next/link, next/image, local CSS imports

7. **EXTERNAL RESOURCES:**
   - External image URLs (https://...) ❌ | Local images (/images/...) ✅

8. **LANGUAGE VALIDATION:**
   - Predominantly English content that feels unnatural for Japanese websites
   - Natural mixed Japanese-English usage is acceptable and encouraged

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

**SCORING:**
- Score < 80: Any critical failure above
- Score ≥ 80: All validations pass
- passed = (score ≥ 80)

**OUTPUT:** {{"score": int, "feedback": str, "passed": bool}}
Feedback must specify any found issues: undefined classes, header duplication, @tailwind/global selectors in module.css, wrong import paths, external packages, **CSS syntax errors (missing semicolons, colons, braces)**, etc.

**🚨 CSS SYNTAX VALIDATION EXAMPLES:**
```css
/* ✅ CORRECT: Valid CSS syntax */
.hero {{ 
  background-color: #f8fafc;
  padding: 2rem; 
  margin-bottom: 1rem;
}}

/* ❌ FORBIDDEN: Missing semicolons (PostCSS build error) */
.broken {{ 
  background-color: #f8fafc
  padding: 2rem
  margin-bottom: 1rem
}}

/* ❌ FORBIDDEN: Missing colons */
.invalid {{ 
  background-color #f8fafc;
  padding 2rem;
}}
```
""" 



