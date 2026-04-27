import { ArtifactType, ARTIFACT_TYPE_CONFIG } from '@/types/artifact';

/**
 * Generate a unique Artifact ID in the format {PREFIX}-{SEQ}
 * e.g. CON-001, CTD-003, EVD-012
 *
 * Stateless: the next sequence number is derived purely from existingIds,
 * so concurrent calls with the same existingIds list are idempotent.
 */
export function generateArtifactId(type: ArtifactType, existingIds: string[] = []): string {
  const prefix = ARTIFACT_TYPE_CONFIG[type].prefix;

  // Find the highest existing sequence number for this prefix
  let maxSeq = 0;
  for (const id of existingIds) {
    if (id.startsWith(prefix + '-')) {
      const seq = parseInt(id.slice(prefix.length + 1), 10);
      if (!isNaN(seq) && seq > maxSeq) maxSeq = seq;
    }
  }

  const nextSeq = maxSeq + 1;
  return `${prefix}-${String(nextSeq).padStart(3, '0')}`;
}

/**
 * Parse artifact type from an artifact ID
 */
export function parseArtifactType(artifactId: string): ArtifactType | null {
  const prefix = artifactId.split('-')[0];
  for (const [type, config] of Object.entries(ARTIFACT_TYPE_CONFIG)) {
    if (config.prefix === prefix) return type as ArtifactType;
  }
  return null;
}
