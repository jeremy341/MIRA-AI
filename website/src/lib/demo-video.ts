export type DemoVideoSource = { src?: string; youtubeId?: string };

const YOUTUBE_ID = /^[A-Za-z0-9_-]{11}$/;

/** True when the id is an 11 character YouTube video id. */
export function isYouTubeId(id: string | undefined): id is string {
  return Boolean(id && YOUTUBE_ID.test(id));
}

/** True when `DemoVideo` will render something: a self-hosted `src` or a valid 11-character `youtubeId`. */
export function hasDemoVideo({ src, youtubeId }: DemoVideoSource): boolean {
  return Boolean(src) || isYouTubeId(youtubeId);
}

/** Privacy-friendly embed address. `autoplay` is only set after the visitor pressed play. */
export function youtubeEmbedUrl(id: string, autoplay = false): string {
  return `https://www.youtube-nocookie.com/embed/${id}${autoplay ? "?autoplay=1" : ""}`;
}
