export const FEATURES = {
  TUTOR_WIZARD: true,
  ACADEMY: false,
  SCHOOL: false,
  SSO: false,
} as const;

export type FeatureKey = keyof typeof FEATURES;
export const isEnabled = (k: FeatureKey) => !!FEATURES[k];
