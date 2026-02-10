// Type declarations for modules without type definitions

declare module '@modelcontextprotocol/sdk' {
  export class MCPClient {
    constructor(config: { serverUrl: string });
    connect(): Promise<void>;
    disconnect(): Promise<void>;
    execute(category: string, tool: string, params: Record<string, any>): Promise<any>;
    listTools(): Promise<Tool[]>;
  }

  export interface Tool {
    name: string;
    description?: string;
    inputSchema?: Record<string, any>;
  }
}

declare module 'swagger-jsdoc' {
  interface Options {
    definition?: Record<string, any>;
    swaggerDefinition?: Record<string, any>;
    apis: string[];
  }
  function swaggerJsdoc(options: Options): Record<string, any>;
  export = swaggerJsdoc;
}

declare module 'swagger-ui-express' {
  import { RequestHandler } from 'express';
  export function setup(swaggerDoc: Record<string, any>, opts?: Record<string, any>): RequestHandler;
  export function serve(req: any, res: any, next: any): void;
  const swaggerUi: { setup: typeof setup; serve: typeof serve };
  export default swaggerUi;
}
