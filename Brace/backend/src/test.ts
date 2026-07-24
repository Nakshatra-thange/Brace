import "dotenv/config";
import { prisma } from "./db/prisma";

async function main() {
  await prisma.$connect();

  console.log("Connected to Neon");

  await prisma.$disconnect();
}

main();