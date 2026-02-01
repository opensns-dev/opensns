// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://opensns-dev.github.io',
	base: '/opensns',
	integrations: [
		starlight({
			title: 'OpenSNS',
			description: 'Open-source AI marketing platform that generates ad creatives from product URLs',
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/opensns/opensns' },
			],
			logo: {
				src: './src/assets/logo.svg',
				replacesTitle: false,
			},
			customCss: ['./src/styles/custom.css'],
			sidebar: [
				{
					label: 'Getting Started',
					items: [
						{ label: 'Introduction', slug: 'getting-started/introduction' },
						{ label: 'Quick Start', slug: 'getting-started/quickstart' },
						{ label: 'Configuration', slug: 'getting-started/configuration' },
					],
				},
				{
					label: 'Guides',
					items: [
						{ label: 'Creating Campaigns', slug: 'guides/campaigns' },
						{ label: 'API Keys Setup', slug: 'guides/api-keys' },
						{ label: 'Web Scraping', slug: 'guides/scraping' },
					],
				},
				{
					label: 'Architecture',
					items: [
						{ label: 'Overview', slug: 'architecture/overview' },
						{ label: 'Agent Pipeline', slug: 'architecture/pipeline' },
						{ label: 'Engine System', slug: 'architecture/engines' },
					],
				},
				{
					label: 'API Reference',
					items: [
						{ label: 'Swagger UI (local)', link: '/opensns/guides/api-keys/#api-documentation' },
					],
				},
				{
					label: 'Deployment',
					items: [
						{ label: 'Docker', slug: 'deployment/docker' },
						{ label: 'Production', slug: 'deployment/production' },
					],
				},
			],
			editLink: {
				baseUrl: 'https://github.com/opensns/opensns/edit/main/docs/',
			},
			lastUpdated: true,
		}),
	],
});
