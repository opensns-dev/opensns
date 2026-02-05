import nextConfig from "eslint-config-next";

const eslintConfig = [
  ...nextConfig,
  {
    ignores: [".next/**", "out/**", "build/**", "next-env.d.ts"],
  },
  {
    // Disable experimental React hooks rules that flag valid patterns
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/purity": "off",
      "react-hooks/immutability": "off",
    },
  },
];

export default eslintConfig;
