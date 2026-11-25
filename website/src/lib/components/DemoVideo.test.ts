import { render } from "svelte/server";
import { describe, expect, it } from "vitest";
import { hasDemoVideo, youtubeEmbedUrl } from "../demo-video";
import DemoVideo from "./DemoVideo.svelte";

const labels = {
  title: "Demo",
  videoCaption: "Caption",
  unsupported: "Unsupported",
  playLabel: "Play video",
  privacyNote: "Loads from YouTube on play.",
};
const html = (props: Record<string, unknown>) => render(DemoVideo, { props: { labels, ...props } }).body;

describe("DemoVideo", () => {
  it("renders nothing while there is neither a src nor a valid YouTube id", () => {
    expect(html({}).replace(/<!--[^>]*-->/g, "")).toBe("");
    expect(html({ youtubeId: "short" }).replace(/<!--[^>]*-->/g, "")).toBe("");
    expect(hasDemoVideo({})).toBe(false);
    expect(hasDemoVideo({ youtubeId: "not-11-chars" })).toBe(false);
  });

  it("renders a player as soon as a source exists", () => {
    expect(hasDemoVideo({ src: "/media/mira-live-demo.mp4" })).toBe(true);
    expect(hasDemoVideo({ youtubeId: "dQw4w9WgXcQ" })).toBe(true);
  });

  it("keeps the self-hosted video as a native <video> without any YouTube request", () => {
    const markup = html({ src: "/media/mira-live-demo.mp4" });
    expect(markup).toContain("<video");
    expect(markup).toContain("/media/mira-live-demo.mp4");
    expect(markup).not.toContain("youtube");
  });

  it("does not load YouTube until the play button is pressed", () => {
    const markup = html({ youtubeId: "dQw4w9WgXcQ" });
    expect(markup).not.toContain("<iframe");
    expect(markup).not.toContain("youtube-nocookie.com/embed");
    expect(markup).toContain("<button");
    expect(markup).toContain('aria-label="Play video: Demo"');
    expect(markup).toContain("Loads from YouTube on play.");
  });

  it("prefers the self-hosted file when both are set", () => {
    const markup = html({ src: "/media/x.mp4", youtubeId: "dQw4w9WgXcQ" });
    expect(markup).toContain("<video");
    expect(markup).not.toContain("<button");
  });

  it("builds the privacy-friendly embed address, with autoplay only after a click", () => {
    expect(youtubeEmbedUrl("dQw4w9WgXcQ")).toBe("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ");
    expect(youtubeEmbedUrl("dQw4w9WgXcQ", true)).toBe("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?autoplay=1");
  });
});
