import fs from "fs";

const files = fs.readdirSync("reports").filter(f => f.endsWith(".txt"));
files.sort((a, b) => fs.statSync(`reports/${b}`).mtimeMs - fs.statSync(`reports/${a}`).mtimeMs);

const rows = files.map(f => {
    const mtime = new Date(fs.statSync(`reports/${f}`).mtime).toLocaleString();
    return `<tr><td><a href="./${f}" target="_blank">${f}</a></td><td>${mtime}</td></tr>`;
});

const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>📊 myKtube 코드 리포트</title>
  <style>
    body { font-family: sans-serif; padding: 2rem; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; }
    th { background: #f5f5f5; }
  </style>
</head>
<body>
  <h1>📊 myKtube 최신 코드 리포트</h1>
  <table>
    <tr><th>파일</th><th>마지막 수정</th></tr>
    ${rows.join("\n")}
  </table>
</body>
</html>
`;

fs.writeFileSync("reports/report-dashboard.html", html, "utf-8");
console.log("✅ report-dashboard.html 생성 완료");
