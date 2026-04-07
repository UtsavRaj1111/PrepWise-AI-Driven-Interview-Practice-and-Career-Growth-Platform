import os
import glob

# Snippets to inject
# 1. Anti-flash script ending head
HEAD_SNIPPET = """    <script>
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    </script>
</head>"""

# 2. Toggle button UI
# We find: `<div style="display: flex; gap: 0.75rem; align-items: center;">`
TOGGLE_UI = """            <div style="display: flex; gap: 0.75rem; align-items: center;">
                <div class="theme-toggle-wrap">
                    <div class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle environment">
                        <i class="fa-solid fa-moon" style="margin-left: 5px;"></i>
                        <i class="fa-solid fa-sun" style="margin-right: 4px;"></i>
                        <div class="orbit"></div>
                    </div>
                </div>"""

# 3. Logic script at the end of body
BODY_END = """    <script>
        function toggleTheme() {
            const html = document.documentElement;
            const target = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', target);
            localStorage.setItem('theme', target);
            window.dispatchEvent(new CustomEvent('themeChanged', { detail: target }));
        }
    </script>
</body>"""

# We'll skip index.html and dashboard.html as they're already done.
skip_files = ['index.html', 'dashboard.html']

for filepath in glob.glob('templates/*.html'):
    basename = os.path.basename(filepath)
    if basename in skip_files: continue

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply anti-flash head
    if '<script>\n        const savedTheme' not in content:
        content = content.replace('</head>', HEAD_SNIPPET, 1)

    # Apply toggle UI
    if 'theme-toggle-wrap' not in content:
        content = content.replace('<div style="display: flex; gap: 0.75rem; align-items: center;">', TOGGLE_UI, 1)

    # Apply logic script
    if 'function toggleTheme()' not in content:
        content = content.replace('</body>', BODY_END, 1)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Injected into all templates.")
