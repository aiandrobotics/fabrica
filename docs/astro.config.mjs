import { createAirStarlightConfig } from '@air-robotics/docs-theme';
import starlight from '@astrojs/starlight';
import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  integrations: [
    starlight(
      createAirStarlightConfig({
        title: 'Fabrica Docs',
        description: 'Documentation for Fabrica — Air Robotics open-source cloth folding robot.',
        githubUrl: 'https://github.com/aiandrobotics/fabrica',
        sidebar: [
          {
            label: 'Fabrica',
            items: [{ autogenerate: { directory: '.' } }],
          },
        ],
      }),
    ),
  ],
});
