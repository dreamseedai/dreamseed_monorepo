const fs = require('fs');
const path = require('path');

const inputDir = path.join(__dirname, '../src/lang');
const outputDir = path.join(__dirname, '../../backend/lang');

if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

fs.readdirSync(inputDir).forEach(file => {
  if (file.endsWith('.ts')) {
    const fullPath = path.join(inputDir, file);
    const content = fs.readFileSync(fullPath, 'utf-8');

    // ⚠️ 'export default { ... };'에서 { ... } 부분만 추출
    const match = content.match(/export\s+default\s+({[\s\S]*});?\s*$/);

    if (!match) {
      console.error(`⚠️ Cannot parse file: ${file}`);
      return;
    }

    const jsonText = match[1];

    try {
      const json = eval('(' + jsonText + ')');
      const langCode = file.replace('.ts', '');
      fs.writeFileSync(
        path.join(outputDir, langCode + '.json'),
        JSON.stringify(json, null, 2),
        'utf-8'
      );
      console.log(`✅ Converted: ${file}`);
    } catch (e) {
      console.error(`❌ Failed to convert: ${file}`, e);
    }
  }
});
