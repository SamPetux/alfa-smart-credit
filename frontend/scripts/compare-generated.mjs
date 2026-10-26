// Сверяет закоммиченные типы API со свежей генерацией из contracts/openapi.json.
import { readFileSync, rmSync } from "node:fs";

const [committedPath, freshPath] = process.argv.slice(2);
const committed = readFileSync(committedPath, "utf8");
const fresh = readFileSync(freshPath, "utf8");
rmSync(freshPath);
if (committed !== fresh) {
  console.error(`${committedPath} устарел относительно contracts/openapi.json. Запустите npm run gen:api.`);
  process.exit(1);
}
console.log("API types match contracts/openapi.json");
