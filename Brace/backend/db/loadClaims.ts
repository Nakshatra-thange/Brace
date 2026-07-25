import "dotenv/config";

import fs from "node:fs";
import path from "node:path";

import {
  PrismaClient,
  ClaimType,
  Section,
} from "../generated/prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const databaseUrl = process.env.DATABASE_URL;

if (!databaseUrl) {
  throw new Error("DATABASE_URL is not set");
}

const prisma = new PrismaClient({
  adapter: new PrismaPg({
    connectionString: databaseUrl,
  }),
});

const OUTPUT_DIR = path.resolve(process.cwd(), "../output");

interface JsonFile {
  filename: string;
  claims: {
    paper: {
      title: string;
      authors: string[];
      year: number | null;
      journal?: string | null;
      doi?: string | null;
    };
    claims: {
      text: string;
      type: string;
      section: string;
      confidence: number;
      evidence?: string;
    }[];
  };
}

function normalizeTitle(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function isValidClaimType(value: string): value is ClaimType {
  return Object.values(ClaimType).includes(value as ClaimType);
}

function isValidSection(value: string): value is Section {
  return Object.values(Section).includes(value as Section);
}

async function loadOne(
  filepath: string,
  existingTitles: Map<string, number>
) {
  const raw = fs.readFileSync(filepath, "utf8");
  const record: JsonFile = JSON.parse(raw);

  if (!record.claims) {
    throw new Error(`Missing "claims" object in ${filepath}`);
  }

  const paper = record.claims.paper;
  const claims = record.claims.claims;

  if (!paper) {
    throw new Error(`Missing paper metadata in ${filepath}`);
  }

  if (!Array.isArray(claims)) {
    throw new Error(`Missing claims array in ${filepath}`);
  }

  const normalized = normalizeTitle(paper.title);

  if (existingTitles.has(normalized)) {
    console.log(
      `[SKIP] ${paper.title} already exists (id=${existingTitles.get(
        normalized
      )})`
    );
    return;
  }

  const cleanClaims = claims.filter((claim) => {
    const ok =
      isValidClaimType(claim.type) &&
      isValidSection(claim.section);

    if (!ok) {
      console.log(
        `[SKIP CLAIM] ${claim.text.substring(0, 60)}...`
      );
    }

    return ok;
  });

  if (cleanClaims.length === 0) {
    console.log(`[SKIP PAPER] ${paper.title} has no valid claims`);
    return;
  }

  const created = await prisma.paper.create({
    data: {
      title: paper.title,
      authors: paper.authors,
      year: paper.year,
      sourceUrl: paper.doi
        ? `https://doi.org/${paper.doi}`
        : null,
      abstract: null,
      rawText: "",

      claims: {
        create: cleanClaims.map((claim) => ({
          text: claim.text,
          claimType: claim.type as ClaimType,
          section: claim.section as Section,
          confidence: claim.confidence,
        })),
      },
    },
    include: {
      claims: true,
    },
  });

  existingTitles.set(normalized, created.id);

  console.log(
    `✓ Inserted "${created.title}" (${created.claims.length} claims)`
  );
}

async function loadAll() {
  if (!fs.existsSync(OUTPUT_DIR)) {
    throw new Error(`Output directory not found: ${OUTPUT_DIR}`);
  }

  const files = fs
    .readdirSync(OUTPUT_DIR)
    .filter((f) => f.endsWith(".json"));

  console.log(`Found ${files.length} JSON files\n`);

  const existing = await prisma.paper.findMany({
    select: {
      id: true,
      title: true,
    },
  });

  const existingTitles = new Map<string, number>();

  for (const paper of existing) {
    existingTitles.set(normalizeTitle(paper.title), paper.id);
  }

  for (const file of files) {
    console.log(`Loading ${file}...`);

    try {
      await loadOne(path.join(OUTPUT_DIR, file), existingTitles);
    } catch (err) {
      console.error(`Failed to load ${file}`);
      console.error(err);
    }
  }
}

loadAll()
  .catch(console.error)
  .finally(async () => {
    await prisma.$disconnect();
  });