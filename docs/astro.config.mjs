// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightBlog from 'starlight-blog';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
	site: 'https://opensns.pages.dev',
	base: '/docs',
	integrations: [
		starlight({
			title: 'OpenSNS',
			description: 'Open-source AI marketing platform that generates ad creatives from product URLs',
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/opensns-dev/opensns' },
			],
			logo: {
				light: './src/assets/logo.svg',
				dark: './src/assets/logo-dark.svg',
				replacesTitle: false,
			},
			favicon: '/favicon.svg',
			customCss: ['./src/styles/custom.css'],
			components: {
				Footer: './src/components/Footer.astro',
			},
			plugins: [
				starlightBlog({
					title: 'Blog',
					authors: {
						opensns: {
							name: 'OpenSNS Team',
							title: 'Open-Source AI Marketing',
							url: 'https://github.com/opensns-dev',
						},
					},
					postCount: 10,
					recentPostCount: 5,
				}),
			],
			head: [
				{
					tag: 'meta',
					attrs: { property: 'og:type', content: 'website' },
				},
				{
					tag: 'meta',
					attrs: { property: 'og:site_name', content: 'OpenSNS' },
				},
				{
					tag: 'meta',
					attrs: { name: 'twitter:card', content: 'summary_large_image' },
				},
			],
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
					{ label: 'Engine Setup', slug: 'guides/engine-setup' },
				],
			},
				{
					label: 'Use Cases',
					items: [
						{ label: 'AI Ads for Agencies', slug: 'use-cases/ai-ads-for-agencies' },
						{ label: 'Naver Ad Automation', slug: 'use-cases/naver-ad-automation' },
						{ label: 'Self-Hosted AI Marketing', slug: 'use-cases/self-hosted-ai-marketing' },
						{ label: 'AI UGC Video Guide', slug: 'use-cases/ai-ugc-video-guide' },
					],
				},
				{
					label: 'Compare',
					items: [
						{ label: 'AI Ad Generators Compared', slug: 'compare/ai-ad-generators' },
						{ label: 'AI UGC Video Tools Compared', slug: 'compare/ai-ugc-video-tools' },
						{ label: 'OpenSNS vs AdCreative.ai', slug: 'compare/opensns-vs-adcreative-ai' },
						{ label: 'OpenSNS vs Zet AI', slug: 'compare/opensns-vs-zet-ai' },
						{ label: 'OpenSNS vs The Brief', slug: 'compare/opensns-vs-the-brief' },
						{ label: 'OpenSNS vs Predis.ai', slug: 'compare/opensns-vs-predis-ai' },
						{ label: 'OpenSNS vs Canva', slug: 'compare/opensns-vs-canva' },
						{ label: 'OpenSNS vs Jasper', slug: 'compare/opensns-vs-jasper' },
						{ label: 'OpenSNS vs Lapis', slug: 'compare/opensns-vs-lapis' },
						{ label: 'OpenSNS vs Creatify', slug: 'compare/opensns-vs-creatify' },
					],
				},
				{
					label: 'Alternatives',
					items: [
						{ label: 'AdCreative.ai Alternatives', slug: 'alternatives/adcreative-ai-alternatives' },
						{ label: 'Zet AI Alternatives', slug: 'alternatives/zet-ai-alternatives' },
						{ label: 'Canva AI Alternatives', slug: 'alternatives/canva-ai-alternatives' },
						{ label: 'Jasper Alternatives', slug: 'alternatives/jasper-alternatives' },
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
					{ label: 'REST API Reference', slug: 'api/reference' },
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
				baseUrl: 'https://github.com/opensns-dev/opensns/edit/main/docs/',
			},
			lastUpdated: true,
		}),
		sitemap(),
	],
});
