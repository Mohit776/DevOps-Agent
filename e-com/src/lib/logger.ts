export const logger = {
  info: (message: string, meta?: any) => {
    console.log(JSON.stringify({ level: 'info', message, timestamp: new Date().toISOString(), ...meta }));
  },
  error: (message: string, error?: any, meta?: any) => {
    console.error(JSON.stringify({ level: 'error', message, error: error instanceof Error ? error.message : error, stack: error instanceof Error ? error.stack : undefined, timestamp: new Date().toISOString(), ...meta }));
  },
  warn: (message: string, meta?: any) => {
    console.warn(JSON.stringify({ level: 'warn', message, timestamp: new Date().toISOString(), ...meta }));
  }
};
