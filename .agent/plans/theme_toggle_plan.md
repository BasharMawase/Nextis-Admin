# Theme Toggle Implementation Plan

## Objective
Implement a fully functional Dark/Light mode toggle for the client page. The default will be the current "Light Mode", and "Dark Mode" will restore the previous dark aesthetic.

## Steps

### 1. Refactor CSS to use Variables
We will define semantic CSS variables for all theme-dependent colors.

```css
:root {
    /* Light Mode (Default) */
    --bg-primary: #f7fafc;
    --bg-secondary: #ffffff;
    --text-primary: #2d3748;
    --text-secondary: #4a5568;
    --text-muted: #718096;
    --accent: #e63946;
    --card-bg: rgba(255, 255, 255, 0.8);
    --card-border: rgba(0, 0, 0, 0.05);
    --card-shadow: rgba(0, 0, 0, 0.05);
    --nav-bg: rgba(255, 255, 255, 0.9);
    --hero-gradient: radial-gradient(circle at top, #ffffff 0%, #edf2f7 100%);
    --section-gradient: linear-gradient(180deg, #f7fafc 0%, #edf2f7 100%);
    --input-bg: #edf2f7;
    --input-border: rgba(0,0,0,0.1);
}

[data-theme="dark"] {
    /* Dark Mode */
    --bg-primary: #1a1d29;
    --bg-secondary: #171b2d;
    --text-primary: #ffffff;
    --text-secondary: #e2e8f0;
    --text-muted: #a0aec0;
    --accent: #e63946;
    --card-bg: rgba(255, 255, 255, 0.03);
    --card-border: rgba(255, 255, 255, 0.05);
    --card-shadow: rgba(0, 0, 0, 0.4);
    --nav-bg: rgba(30, 35, 48, 0.9);
    --hero-gradient: radial-gradient(circle at top, #2d3748 0%, #1a1d29 100%);
    --section-gradient: linear-gradient(180deg, #171b2d 0%, #1a1d29 100%);
    --input-bg: rgba(0,0,0,0.2);
    --input-border: rgba(255,255,255,0.1);
}
```

### 2. Clean Up HTML Inline Styles
The current HTML has many hardcoded inline styles (e.g., `style="background: #ffffff"`). These MUST be removed or replaced with classes that use the variables above.

**Target Areas:**
- `<body>`
- `.hero-section`
- `#services`, `#portfolio`, `#contact`
- Footer
- Cards and Forms

### 3. Update CSS Classes
Update existing classes in `<style>` to reference the variables.

**Example:**
```css
body {
    background-color: var(--bg-primary);
    color: var(--text-primary);
}
.service-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    box-shadow: 0 10px 30px var(--card-shadow);
}
```

### 4. Create Toggle Button
Add a fixed or navbar button to switch themes.

```html
<button id="themeToggle" class="theme-btn" onclick="toggleTheme()">
    🌙
</button>
```

### 5. Add JavaScript Logic
```javascript
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateIcon(next);
}
```

## Execution Strategy
1.  **CSS Refactor**: Add variables and update main styles. [COMPLETED]
2.  **HTML Cleanup**: Systematic removal of inline background colors. [COMPLETED]
3.  **UI/JS**: Add button and script. [COMPLETED]

**Status: COMPLETED**
