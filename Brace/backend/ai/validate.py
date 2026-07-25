from dataclasses import dataclass, field

ALLOWED_CLAIM_TYPES = {"EMPIRICAL", "THEORETICAL", "METHODOLOGICAL"}
ALLOWED_SECTIONS = {"ABSTRACT", "INTRODUCTION", "RESULTS", "DISCUSSION", "CONCLUSION"}

@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cleaned: dict | None = None


def validate_extraction(parsed: dict) -> ValidationResult:
    """
    Validates Claude's extraction output against the Prisma schema's
    enum constraints and required shape, BEFORE anything touches the DB.

    - errors: hard failures, this paper should not be inserted as-is
    - warnings: soft issues (missing metadata etc.), safe to insert but flag for review
    """
    errors = []
    warnings = []

    if "paper" not in parsed or "claims" not in parsed:
        return ValidationResult(valid=False, errors=["Missing 'paper' or 'claims' key"])

    paper = parsed["paper"]
    claims = parsed["claims"]

    # --- paper metadata checks (soft) ---
    if not paper.get("title"):
        warnings.append("Missing title")
    if not paper.get("authors"):
        warnings.append("Missing or empty authors list")
    if not paper.get("year"):
        warnings.append("Missing year")

    # --- claims checks (hard) ---
    if not isinstance(claims, list) or len(claims) == 0:
        errors.append("Claims must be a non-empty list")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    cleaned_claims = []
    for i, claim in enumerate(claims):
        claim_errors = []

        text = claim.get("text", "").strip()
        if not text:
            claim_errors.append(f"Claim {i}: empty text")

        claim_type = str(claim.get("type", "")).upper().strip()
        if claim_type not in ALLOWED_CLAIM_TYPES:
            claim_errors.append(
                f"Claim {i}: invalid type '{claim.get('type')}' — must be one of {ALLOWED_CLAIM_TYPES}"
            )

        section = str(claim.get("section", "")).upper().strip()
        if section not in ALLOWED_SECTIONS:
            claim_errors.append(
                f"Claim {i}: invalid section '{claim.get('section')}' — must be one of {ALLOWED_SECTIONS}"
            )

        confidence = claim.get("confidence")
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            claim_errors.append(f"Claim {i}: confidence must be a float 0-1, got {confidence}")

        if claim_errors:
            errors.extend(claim_errors)
            continue  # skip this claim, don't add to cleaned set

        cleaned_claims.append({
            "text": text,
            "type": claim_type,       # normalized uppercase — safe for Prisma enum
            "section": section,       # normalized uppercase — safe for Prisma enum
            "confidence": float(confidence),
            "evidence": claim.get("evidence", "").strip(),
        })

    if not cleaned_claims:
        errors.append("No valid claims survived validation")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    if len(cleaned_claims) < len(claims):
        warnings.append(
            f"{len(claims) - len(cleaned_claims)} of {len(claims)} claims were dropped due to validation errors"
        )

    cleaned = {
        "paper": {
            "title": paper.get("title") or "UNKNOWN TITLE",
            "authors": paper.get("authors") or [],
            "year": paper.get("year"),
            "journal": paper.get("journal"),
            "doi": paper.get("doi"),
        },
        "claims": cleaned_claims,
    }

    return ValidationResult(valid=True, errors=errors, warnings=warnings, cleaned=cleaned)