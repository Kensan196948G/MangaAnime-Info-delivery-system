// Pre-initialization hook
console.log('[Hook] Pre-initialization: Loading environment...');

const context = JSON.parse(process.env.HOOK_CONTEXT || '{}');
console.log('[Hook] Context:', context);

// Add your pre-init logic here
process.exit(0);
