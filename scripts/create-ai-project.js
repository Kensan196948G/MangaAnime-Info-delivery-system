#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const args = process.argv.slice(2);
const projectPath = args[0];

if (!projectPath) {
  console.error('Usage: create-ai-project <project-path>');
  process.exit(1);
}

const absolutePath = path.isAbsolute(projectPath) 
  ? projectPath 
  : path.join(process.cwd(), projectPath);

const projectName = path.basename(absolutePath);
const templateDir = '/mnt/Linux-ExHDD/Claude-GlobalSettings';

console.log(`🚀 Creating AI-enabled project: ${projectName}`);
console.log(`   Location: ${absolutePath}`);
console.log('');

// 1. Create project directory
console.log('📁 Creating project structure...');
fs.mkdirSync(absolutePath, { recursive: true });

// 2. Copy entire .claude directory
const claudeSource = path.join(templateDir, '.claude');
const claudeTarget = path.join(absolutePath, '.claude');
copyDirectory(claudeSource, claudeTarget);
console.log('✓ Copied .claude configuration');

// 3. Copy essential files
const filesToCopy = [
  'package.json',
  'README.md',
  '.env.example'
];

filesToCopy.forEach(file => {
  const source = path.join(templateDir, file);
  const target = path.join(absolutePath, file);
  
  if (fs.existsSync(source)) {
    if (file === 'package.json') {
      // Customize package.json
      const packageJson = JSON.parse(fs.readFileSync(source, 'utf-8'));
      packageJson.name = projectName.toLowerCase().replace(/\s+/g, '-');
      packageJson.version = '1.0.0';
      packageJson.description = `${projectName} with AI Development Environment`;
      fs.writeFileSync(target, JSON.stringify(packageJson, null, 2));
    } else if (file === '.env.example') {
      fs.copyFileSync(source, path.join(absolutePath, '.env'));
    } else {
      fs.copyFileSync(source, target);
    }
    console.log(`✓ Created ${file}`);
  }
});

// 4. Copy directories
const directoriesToCopy = ['scripts', 'config', 'src'];
directoriesToCopy.forEach(dir => {
  const source = path.join(templateDir, dir);
  const target = path.join(absolutePath, dir);
  
  if (fs.existsSync(source)) {
    copyDirectory(source, target);
    console.log(`✓ Copied ${dir}/`);
  }
});

// 5. Update project-specific configuration
const projectConfig = path.join(claudeTarget, 'project-config.json');
if (fs.existsSync(projectConfig)) {
  const config = JSON.parse(fs.readFileSync(projectConfig, 'utf-8'));
  config.name = projectName;
  config.projectPath = absolutePath;
  config.createdAt = new Date().toISOString();
  fs.writeFileSync(projectConfig, JSON.stringify(config, null, 2));
  console.log('✓ Updated project configuration');
}

// 6. Initialize git (optional)
try {
  execSync('git init', { cwd: absolutePath, stdio: 'ignore' });
  
  // Create .gitignore
  const gitignore = `node_modules/
.env
dist/
*.log
.DS_Store
.claude/reports/
.claude/memory.db`;
  
  fs.writeFileSync(path.join(absolutePath, '.gitignore'), gitignore);
  console.log('✓ Initialized git repository');
} catch (error) {
  console.log('⚠️  Git initialization skipped');
}

// 7. Install dependencies
console.log('\n📦 Installing dependencies...');
try {
  execSync('npm install --no-optional', { 
    cwd: absolutePath, 
    stdio: 'inherit' 
  });
  console.log('✓ Dependencies installed');
} catch (error) {
  console.log('⚠️  Some dependencies failed (run npm install manually)');
}

// Helper function to copy directories recursively
function copyDirectory(source, target) {
  if (!fs.existsSync(source)) return;
  
  fs.mkdirSync(target, { recursive: true });
  
  const files = fs.readdirSync(source);
  files.forEach(file => {
    const sourcePath = path.join(source, file);
    const targetPath = path.join(target, file);
    
    const stat = fs.statSync(sourcePath);
    if (stat.isDirectory()) {
      copyDirectory(sourcePath, targetPath);
    } else {
      fs.copyFileSync(sourcePath, targetPath);
    }
  });
}

console.log('\n' + '='.repeat(60));
console.log('🎉 Project created successfully!');
console.log('='.repeat(60));
console.log('');
console.log(`Next steps:`);
console.log(`  cd ${projectPath}`);
console.log(`  npm start`);
console.log('');
console.log('All AI features are enabled and ready to use!');
console.log('');
console.log('Available commands:');
console.log('  npm start           - Start all systems');
console.log('  npm run dev         - Development mode');
console.log('  npm run claude-flow - Claude-Flow swarm');
console.log('  npm run status      - Check system status');