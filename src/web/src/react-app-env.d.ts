/// <reference types="react-scripts" />

// This file extends the global namespace with custom type definitions for various file formats, 
// modules, and libraries used in the Molecular Data Management and CRO Integration Platform frontend.

// Static Asset Imports
declare module '*.svg' {
  const content: React.FunctionComponent<React.SVGAttributes<SVGElement>>;
  export default content;
}
declare module '*.png' {
  const content: string;
  export default content;
}
declare module '*.jpg' {
  const content: string;
  export default content;
}
declare module '*.jpeg' {
  const content: string;
  export default content;
}
declare module '*.gif' {
  const content: string;
  export default content;
}
declare module '*.webp' {
  const content: string;
  export default content;
}
declare module '*.ico' {
  const content: string;
  export default content;
}
declare module '*.bmp' {
  const content: string;
  export default content;
}

// Style Imports
declare module '*.css' {
  const content: { [className: string]: string };
  export default content;
}
declare module '*.scss' {
  const content: { [className: string]: string };
  export default content;
}
declare module '*.sass' {
  const content: { [className: string]: string };
  export default content;
}
declare module '*.less' {
  const content: { [className: string]: string };
  export default content;
}

// Data File Imports
declare module '*.json' {
  const content: any;
  export default content;
}
declare module '*.mol' {
  const content: string;
  export default content;
}
declare module '*.sdf' {
  const content: string;
  export default content;
}

// ChemDoodle Global
declare global {
  interface Window {
    ChemDoodle: any;
  }
}

// Environment Variables
interface ImportMetaEnv {
  VITE_API_URL: string;
  VITE_AI_ENGINE_URL: string;
  VITE_AUTH_DOMAIN: string; 
  VITE_APP_VERSION: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}