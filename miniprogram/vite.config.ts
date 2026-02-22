import { defineConfig } from 'weapp-vite/config'
import { UnifiedViteWeappTailwindcssPlugin } from 'weapp-tailwindcss/vite'

export default defineConfig(
  () => {
    return {
      weapp: {
        srcRoot: 'src',
        generate: {
          extensions: {
            js: 'ts',
            wxss: 'scss',
          },
          dirs: {
            component: 'src/components',
            page: 'src/pages',
          },
        },
      },
      css: {
        preprocessorOptions: {
          scss: {
            silenceDeprecations: ['legacy-js-api', 'import'],
          },
        },
      },
      plugins: [
        UnifiedViteWeappTailwindcssPlugin({
          injectAdditionalCssVarScope: true,
        }),
      ],
    }
  },
)
