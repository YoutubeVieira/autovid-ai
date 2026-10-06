// Structure schema.org/Recipe (JSON-LD) pour les vidéos de recettes.
// Durées au format ISO 8601 (ex. "PT15M").

export const RECIPE_FIELDS = [
  'name',
  'image',
  'author',
  'description',
  'prepTime',
  'cookTime',
  'totalTime',
  'recipeYield',
  'recipeIngredient',
  'recipeInstructions',
  'video',
];

const toIsoDuration = (minutes) => {
  if (minutes == null) return undefined;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `PT${h ? `${h}H` : ''}${m || !h ? `${m}M` : ''}`;
};

export function buildRecipeSchema({
  name,
  image,
  author,
  description,
  prepMinutes,
  cookMinutes,
  recipeYield,
  ingredients = [],
  steps = [],
  video,
}) {
  const totalMinutes =
    prepMinutes != null || cookMinutes != null
      ? (prepMinutes || 0) + (cookMinutes || 0)
      : undefined;

  return {
    '@context': 'https://schema.org',
    '@type': 'Recipe',
    name,
    image: Array.isArray(image) ? image : image ? [image] : [],
    author: author ? { '@type': 'Person', name: author } : undefined,
    description,
    prepTime: toIsoDuration(prepMinutes),
    cookTime: toIsoDuration(cookMinutes),
    totalTime: toIsoDuration(totalMinutes),
    recipeYield,
    recipeIngredient: ingredients,
    recipeInstructions: steps.map((text) => ({ '@type': 'HowToStep', text })),
    video: video
      ? {
          '@type': 'VideoObject',
          name: video.name || name,
          description: video.description || description,
          thumbnailUrl: video.thumbnailUrl,
          contentUrl: video.contentUrl,
          uploadDate: video.uploadDate,
          duration: video.duration,
        }
      : undefined,
  };
}
