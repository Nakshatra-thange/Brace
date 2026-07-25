-- CreateEnum
CREATE TYPE "ClaimType" AS ENUM ('EMPIRICAL', 'THEORETICAL', 'METHODOLOGICAL');

-- CreateEnum
CREATE TYPE "Section" AS ENUM ('ABSTRACT', 'INTRODUCTION', 'RESULTS', 'DISCUSSION', 'CONCLUSION');

-- CreateEnum
CREATE TYPE "RelationshipType" AS ENUM ('AGREES', 'CONTRADICTS', 'SUPERSEDES', 'SUPPORTS', 'UNRELATED');

-- CreateEnum
CREATE TYPE "EmbeddingProvider" AS ENUM ('SPECTER2', 'VOYAGE', 'OPENAI');

-- CreateTable
CREATE TABLE "Paper" (
    "id" SERIAL NOT NULL,
    "title" TEXT NOT NULL,
    "authors" TEXT[],
    "year" INTEGER,
    "sourceUrl" TEXT,
    "abstract" TEXT,
    "rawText" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Paper_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Claim" (
    "id" SERIAL NOT NULL,
    "paperId" INTEGER NOT NULL,
    "text" TEXT NOT NULL,
    "claimType" "ClaimType" NOT NULL,
    "section" "Section" NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Claim_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ClaimEmbedding" (
    "id" SERIAL NOT NULL,
    "claimId" INTEGER NOT NULL,
    "provider" "EmbeddingProvider" NOT NULL,
    "dimensions" INTEGER NOT NULL,
    "vector" vector NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ClaimEmbedding_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ClaimRelationship" (
    "id" SERIAL NOT NULL,
    "sourceClaimId" INTEGER NOT NULL,
    "targetClaimId" INTEGER NOT NULL,
    "relationship" "RelationshipType" NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "reasoning" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ClaimRelationship_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "Paper_year_idx" ON "Paper"("year");

-- CreateIndex
CREATE INDEX "Claim_paperId_idx" ON "Claim"("paperId");

-- CreateIndex
CREATE UNIQUE INDEX "ClaimEmbedding_claimId_key" ON "ClaimEmbedding"("claimId");

-- CreateIndex
CREATE INDEX "ClaimRelationship_sourceClaimId_idx" ON "ClaimRelationship"("sourceClaimId");

-- CreateIndex
CREATE INDEX "ClaimRelationship_targetClaimId_idx" ON "ClaimRelationship"("targetClaimId");

-- CreateIndex
CREATE UNIQUE INDEX "ClaimRelationship_sourceClaimId_targetClaimId_key" ON "ClaimRelationship"("sourceClaimId", "targetClaimId");

-- AddForeignKey
ALTER TABLE "Claim" ADD CONSTRAINT "Claim_paperId_fkey" FOREIGN KEY ("paperId") REFERENCES "Paper"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ClaimEmbedding" ADD CONSTRAINT "ClaimEmbedding_claimId_fkey" FOREIGN KEY ("claimId") REFERENCES "Claim"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ClaimRelationship" ADD CONSTRAINT "ClaimRelationship_sourceClaimId_fkey" FOREIGN KEY ("sourceClaimId") REFERENCES "Claim"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ClaimRelationship" ADD CONSTRAINT "ClaimRelationship_targetClaimId_fkey" FOREIGN KEY ("targetClaimId") REFERENCES "Claim"("id") ON DELETE CASCADE ON UPDATE CASCADE;
