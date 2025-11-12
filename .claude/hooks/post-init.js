// Post-initialization hook
console.log('[Hook] Post-initialization: System ready!');

const context = JSON.parse(process.env.HOOK_CONTEXT || '{}');

// Add your post-init logic here
process.exit(0);
