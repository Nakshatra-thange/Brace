import fs from "fs";
import path from "path";
import { PrismaClient, ClaimType, Section } from "../generated/prisma/client.ts";
import { PrismaPg } from "@prisma/adapter-pg";
const prisma = new PrismaClient({
  adapter: new PrismaPg({
    connectionString: process.env.DATABASE_URL!,
  }),
});
const OUTPUT_DIR = path.resolve(process.cwd(), "output");

interface ValidatedRecord {
  filename: string;
  errors: string[];
  warnings: string[];
  data: {
    paper: {
      title: string;
      authors: string[];
      year: number | null;
      journal: string | null;
      doi: string | null;
    };
    claims: {
      text: string;
      type: string;
      section: string;
      confidence: number;
      evidence: string;
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

function isValidClaimType(t: string): t is ClaimType {
  return Object.values(ClaimType).includes(t as ClaimType);
}

function isValidSection(s: string): s is Section {
  return Object.values(Section).includes(s as Section);
}

async function loadOne(filepath: string, existingTitles: Map<string, number>) {
  const raw = fs.readFileSync(filepath, "utf-8");
  const record: ValidatedRecord = JSON.parse(raw);
  const { paper, claims } = record.data;

  const normTitle = normalizeTitle(paper.title);

  if (existingTitles.has(normTitle)) {
    console.log(
      `[SKIP - DUPLICATE] "${paper.title}" matches existing paper id ${existingTitles.get(normTitle)}`
    );
    return;
  }

  // Filter claims to only those matching Prisma enums (belt-and-suspenders —
  // Python validator already did this, but the DB layer shouldn't trust it blindly)
  const cleanClaims = claims.filter((c) => {
    const okType = isValidClaimType(c.type);
    const okSection = isValidSection(c.section);
    if (!okType || !okSection) {
      console.log(
        `[SKIP CLAIM] "${paper.title}" — bad enum type="${c.type}" section="${c.section}"`
      );
    }
    return okType && okSection;
  });

  if (cleanClaims.length === 0) {
    console.log(`[SKIP PAPER] "${paper.title}" — no valid claims after enum check`);
    return;
  }

  const created = await prisma.paper.create({
    data: {
      title: paper.title,
      authors: paper.authors ?? [],
      year: paper.year ?? undefined,
      sourceUrl: paper.doi ? `https://doi.org/${paper.doi}` : undefined,
      abstract: undefined, // not extracted separately yet — fine for now
      rawText: "", // TODO: wire in full extracted text if you want it stored
      claims: {
        create: cleanClaims.map((c) => ({
          text: c.text,
          claimType: c.type as ClaimType,
          section: c.section as Section,
          confidence: c.confidence,
        })),
      },
    },
    include: { claims: true },
  });

  existingTitles.set(normTitle, created.id);
  console.log(`[INSERTED] "${paper.title}" — id ${created.id}, ${created.claims.length} claims`);
}

async function loadAll() {
  const files = fs
    .readdirSync(VALIDATED_DIR)
    .filter((f) => f.endsWith(".json"));

  console.log(`Found ${files.length} validated files to load.\n`);

  // preload existing papers so dedup works across runs, not just within one run
  const existing = await prisma.paper.findMany({ select: { id: true, title: true } });
  const existingTitles = new Map<string, number>();
  for (const p of existing) {
    existingTitles.set(normalizeTitle(p.title), p.id);
  }

  for (const file of files) {
    await loadOne(path.join(VALIDATED_DIR, file), existingTitles);
  }

  await prisma.$disconnect();
}

loadAll().catch((e) => {
  console.error(e);
  prisma.$disconnect();
  process.exit(1);
});