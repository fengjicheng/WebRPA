#!/usr/bin/env node

/**
 * WebRPA 离线部署验证脚本
 * 
 * 此脚本会检查项目中是否还有外部CDN引用
 */

const fs = require('fs');
const path = require('path');

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

// 需要检查的CDN域名
const cdnDomains = [
  'cdn.jsdelivr.net',
  'unpkg.com',
  'cdnjs.cloudflare.com',
  'fonts.googleapis.com',
  'fonts.gstatic.com',
];

// 需要检查的文件扩展名
const fileExtensions = ['.html', '.js', '.jsx', '.ts', '.tsx', '.css', '.json'];

// 排除的目录
const excludeDirs = ['node_modules', '.git', 'dist', 'build', 'Python313', 'Python312', 'Python311'];

// 排除的文件（这些文件中的CDN引用是安全的）
const excludeFiles = [
  'OFFLINE_VERIFICATION.md',
  'verify-offline.js',
  'test-monaco-offline.html',
];

let totalFiles = 0;
let checkedFiles = 0;
let issues = [];

/**
 * 检查文件内容
 */
function checkFile(filePath) {
  const relativePath = path.relative(process.cwd(), filePath);
  
  // 跳过排除的文件
  if (excludeFiles.some(excluded => relativePath.includes(excluded))) {
    return;
  }
  
  checkedFiles++;
  
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    
    // 检查每个CDN域名
    cdnDomains.forEach(domain => {
      if (content.includes(domain)) {
        // 检查是否在注释或文档中
        const lines = content.split('\n');
        lines.forEach((line, index) => {
          if (line.includes(domain)) {
            // 简单判断：如果在注释中，可能是安全的
            const isComment = 
              line.trim().startsWith('//') || 
              line.trim().startsWith('*') ||
              line.trim().startsWith('<!--') ||
              line.includes('* ') ||
              relativePath.includes('documentation');
            
            if (!isComment) {
              issues.push({
                file: relativePath,
                line: index + 1,
                domain: domain,
                content: line.trim(),
              });
            }
          }
        });
      }
    });
  } catch (error) {
    log(`⚠️  无法读取文件: ${relativePath}`, 'yellow');
  }
}

/**
 * 递归扫描目录
 */
function scanDirectory(dir) {
  const items = fs.readdirSync(dir);
  
  items.forEach(item => {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory()) {
      // 跳过排除的目录
      if (!excludeDirs.includes(item)) {
        scanDirectory(fullPath);
      }
    } else if (stat.isFile()) {
      totalFiles++;
      const ext = path.extname(item);
      if (fileExtensions.includes(ext)) {
        checkFile(fullPath);
      }
    }
  });
}

/**
 * 主函数
 */
function main() {
  log('\n🔍 WebRPA 离线部署验证', 'cyan');
  log('━'.repeat(50), 'cyan');
  
  log('\n📋 检查配置:', 'blue');
  log(`   - 检查的CDN域名: ${cdnDomains.length}个`, 'blue');
  log(`   - 检查的文件类型: ${fileExtensions.join(', ')}`, 'blue');
  log(`   - 排除的目录: ${excludeDirs.join(', ')}`, 'blue');
  
  log('\n🔎 开始扫描...', 'yellow');
  
  const startTime = Date.now();
  scanDirectory(process.cwd());
  const endTime = Date.now();
  
  log('\n📊 扫描结果:', 'blue');
  log(`   - 总文件数: ${totalFiles}`, 'blue');
  log(`   - 已检查: ${checkedFiles}`, 'blue');
  log(`   - 耗时: ${endTime - startTime}ms`, 'blue');
  
  if (issues.length === 0) {
    log('\n✅ 太棒了！没有发现外部CDN引用！', 'green');
    log('   项目已完全离线化，可以在纯内网环境中使用。', 'green');
  } else {
    log(`\n⚠️  发现 ${issues.length} 个潜在的外部引用：`, 'yellow');
    log('━'.repeat(50), 'yellow');
    
    issues.forEach((issue, index) => {
      log(`\n${index + 1}. ${issue.file}:${issue.line}`, 'red');
      log(`   域名: ${issue.domain}`, 'red');
      log(`   内容: ${issue.content.substring(0, 100)}...`, 'red');
    });
    
    log('\n💡 提示:', 'cyan');
    log('   - 如果这些引用在文档或注释中，可以忽略', 'cyan');
    log('   - 如果是实际的资源加载，需要修改为本地引用', 'cyan');
    log('   - 可以使用浏览器开发者工具的Network标签页验证', 'cyan');
  }
  
  log('\n📖 详细文档:', 'blue');
  log('   请查看 OFFLINE_VERIFICATION.md 了解更多信息', 'blue');
  
  log('\n━'.repeat(50), 'cyan');
  log('验证完成！\n', 'cyan');
  
  // 返回退出码
  process.exit(issues.length > 0 ? 1 : 0);
}

// 运行
main();
