import fs from "fs";
import path from "path";

const reportsDir = path.resolve("reports");
const summaryFile = path.join(reportsDir, "report-summary.md");

const files = fs.readdirSync(reportsDir).filter(f =>
    f.endsWith(".txt") && !f.startsWith("latest")
);

files.sort((a, b) => fs.statSync(path.join(reportsDir, b)).mtimeMs - fs.statSync(path.join(reportsDir, a)).mtimeMs);

const summaryLines = [
    "# 📋 최신 코드 리포트 요약",
    "",
    "| 파일 | 마지막 수정 시간 |",
    "|------|------------------|"
];

files.forEach(file => {
    const stats = fs.statSync(path.join(reportsDir, file));
    const modified = new Date(stats.mtime).toLocaleString();
    summaryLines.push(`| [${file}](./${file}) | ${modified} |`);
});

// 저장
fs.writeFileSync(summaryFile, summaryLines.join("\n"), "utf-8");

console.log("✅ report-summary.md 생성 완료");
