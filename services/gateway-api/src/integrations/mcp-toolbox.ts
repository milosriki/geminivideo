import { MCPClient, Tool } from '@modelcontextprotocol/sdk';

/**
 * MCP Toolbox Integration
 *
 * Provides Model Context Protocol (MCP) client integration for database operations
 * and other MCP server functionality. This enables AI agents to interact with
 * external tools and data sources through a standardized protocol.
 */

// Initialize MCP client with server URL from environment
export const mcpClient = new MCPClient({
  serverUrl: process.env.MCP_SERVER_URL || 'http://localhost:3000',
});

/**
 * Database tools wrapper for MCP operations
 * Provides convenient methods for common database operations through MCP
 */
export const dbTools = {
  /**
   * Execute a SQL query through MCP
   * @param sql - SQL query string to execute
   * @returns Query results from the MCP database server
   */
  queryDatabase: async (sql: string) => {
    try {
      return await mcpClient.execute('database', 'query', { sql });
    } catch (error) {
      console.error('MCP database query error:', error);
      throw error;
    }
  },

  /**
   * Insert a record into a table through MCP
   * @param table - Table name to insert into
   * @param data - Data object to insert
   * @returns Insert operation result
   */
  insertRecord: async (table: string, data: any) => {
    try {
      return await mcpClient.execute('database', 'insert', { table, data });
    } catch (error) {
      console.error('MCP database insert error:', error);
      throw error;
    }
  },

  /**
   * Update records in a table through MCP
   * @param table - Table name to update
   * @param data - Data object with values to update
   * @param where - Where clause conditions
   * @returns Update operation result
   */
  updateRecord: async (table: string, data: any, where: any) => {
    try {
      return await mcpClient.execute('database', 'update', { table, data, where });
    } catch (error) {
      console.error('MCP database update error:', error);
      throw error;
    }
  },

  /**
   * Delete records from a table through MCP
   * @param table - Table name to delete from
   * @param where - Where clause conditions
   * @returns Delete operation result
   */
  deleteRecord: async (table: string, where: any) => {
    try {
      return await mcpClient.execute('database', 'delete', { table, where });
    } catch (error) {
      console.error('MCP database delete error:', error);
      throw error;
    }
  },
};

/**
 * Get all available MCP tools
 * @returns List of available MCP tools
 */
export const getAvailableTools = async (): Promise<Tool[]> => {
  try {
    return await mcpClient.listTools();
  } catch (error) {
    console.error('Error fetching MCP tools:', error);
    return [];
  }
};

/**
 * Execute a custom MCP tool
 * @param toolName - Name of the tool to execute
 * @param toolCategory - Category/namespace of the tool
 * @param params - Parameters to pass to the tool
 * @returns Tool execution result
 */
export const executeTool = async (
  toolCategory: string,
  toolName: string,
  params: Record<string, any>
) => {
  try {
    return await mcpClient.execute(toolCategory, toolName, params);
  } catch (error) {
    console.error(`Error executing MCP tool ${toolCategory}:${toolName}:`, error);
    throw error;
  }
};

/**
 * Initialize MCP client connection
 * Should be called on application startup
 */
export const initializeMCP = async (): Promise<void> => {
  try {
    await mcpClient.connect();
    console.log('MCP client connected successfully');
  } catch (error) {
    console.error('Failed to initialize MCP client:', error);
    throw error;
  }
};

/**
 * Close MCP client connection
 * Should be called on application shutdown
 */
export const closeMCP = async (): Promise<void> => {
  try {
    await mcpClient.disconnect();
    console.log('MCP client disconnected');
  } catch (error) {
    console.error('Error disconnecting MCP client:', error);
  }
};

export default {
  mcpClient,
  dbTools,
  getAvailableTools,
  executeTool,
  initializeMCP,
  closeMCP,
};
