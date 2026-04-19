export const ARCHETYPE_CONFIG: Record<string, {
  icon: string;
  color: string;
  border: string;
  bg: string;
  text: string;
  timing: string;
  tips: string[];
}> = {
  "Flash Viral": {
    icon: "⚡",
    color: "#ff3333",
    border: "#ff3333",
    bg: "#1a0000",
    text: "#ff6666",
    timing: "< 24 hours",
    tips: [
      "Post within the next 6–12 hours — this trend peaks fast and collapses.",
      "Use a clickbait-adjacent title with the trending keyword front-loaded.",
      "Keep the video under 8 minutes to maximise watch-through rate.",
      "Pin a comment driving viewers to your other content immediately.",
      "Don't invest heavy production — speed beats polish here.",
    ],
  },
  "Fast Mover": {
    icon: "🚀",
    color: "#ff8800",
    border: "#ff8800",
    bg: "#1a0d00",
    text: "#ffaa44",
    timing: "48 hours",
    tips: [
      "Publish within 48 hours or the window closes.",
      "Front-load your hook in the first 15 seconds — retention is everything.",
      "Add 10–15 targeted tags using the exact trending search terms.",
      "Share across all your community channels the moment you go live.",
      "Set up an end-screen pointing to your next planned video now.",
    ],
  },
  "Mid-Burn Trending": {
    icon: "🔥",
    color: "#ffcc00",
    border: "#ffcc00",
    bg: "#1a1a00",
    text: "#ffdd44",
    timing: "3–5 days",
    tips: [
      "You have a 3–5 day window — take a day to improve production quality.",
      "Aim for a more comprehensive take: go deeper than the initial viral clips.",
      "A/B test your thumbnail in the first 2 hours using YouTube's built-in tool.",
      "Collaborate or react to another creator in this niche for extra reach.",
      "Upload a Shorts version to capture the algorithm's cross-format boost.",
    ],
  },
  "Sustained Grower": {
    icon: "📈",
    color: "#00cc66",
    border: "#00cc66",
    bg: "#001a00",
    text: "#44ffaa",
    timing: "1+ week",
    tips: [
      "Publish steadily — consistency matters more than timing for this archetype.",
      "Optimise for SEO: focus on long-tail keywords in title, description, and tags.",
      "Build a series or playlist around this topic to compound view sessions.",
      "Answer viewer questions in your comments to boost engagement signals.",
      "Link to complementary videos in your description to reduce bounce rate.",
    ],
  },
  "Legacy Evergreen": {
    icon: "🌿",
    color: "#3399ff",
    border: "#3399ff",
    bg: "#00001a",
    text: "#66bbff",
    timing: "Anytime",
    tips: [
      "Prioritise depth and production value — this video will live for years.",
      "Target a 15-30 minute run-time: watchers want comprehensive coverage.",
      "Update the title and thumbnail every 6-12 months to stay fresh in search.",
      "Build internal links: reference this video in every related upload.",
      "Monetise via mid-roll ads — high CPM on long-watch evergreen content.",
    ],
  },
};

export const DOW_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export const ARCHETYPES_LIST = [
  { name: "Flash Viral",       desc: "Explodes in 24 hours. Act now or skip." },
  { name: "Fast Mover",        desc: "Narrow 48-hour publish window." },
  { name: "Mid-Burn Trending", desc: "3–5 day opportunity. Polish counts." },
  { name: "Sustained Grower",  desc: "Week-long window. SEO matters." },
  { name: "Legacy Evergreen",  desc: "Publish anytime. Think long-term." },
];