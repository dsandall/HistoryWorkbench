// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { resolve } from 'path';
import { fileURLToPath } from 'url';

// https://astro.build/config
export default defineConfig({
    site: "https://eblanshey.github.io",
    base: "/HistoryWorkbench",
    vite: {
        server: {
            fs: {
                // Allow the project root so the favicon.svg symlink to freecad/history_wb/resources/icons/ resolves correctly.
                allow: [resolve(fileURLToPath(import.meta.url), "..")],
            },
        },
    },
    integrations: [
        starlight({
            title: "History Workbench",
            logo: {
                src: "./public/icons/Logo.svg",
            },
            social: [{ icon: "github", label: "GitHub", href: "https://github.com/eblanshey/HistoryWorkbench" }],
            sidebar: [
                { slug: "user-guide/quick-start" },
                {
                    label: "Guide",
                    items: [
                        "user-guide/installation",
                        "user-guide/first-steps",
                        "user-guide/concepts",
                        "user-guide/daily-usage",
                        "user-guide/faq",
                        "user-guide/advanced-usage",
                    ],
                },
                {
                    label: "Reference",
                    items: ["reference/configuration", "reference/commands"],
                },
                {
                    label: "Development",
                    collapsed: true,
                    items: [
                        {
                            autogenerate: {
                                directory: "development",
                                collapsed: true,
                            },
                        },
                    ],
                },
            ],
        }),
    ],
});
