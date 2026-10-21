# Rabbit Hole Archives — Visual Style Guide

**Status:** Approved direction / evolving specification  
**Version:** 1.0  
**Date:** October 20, 2026  
**Project:** Rabbit Hole Archives (working title)  
**Visual reference:** `docs/design/references/approved-moodboard.png` (reference retained as a separate design asset)

> **Some questions lead further down.**

## 1. Creative north star

**Cinematic noir × tactile detective archives × restrained Bunnyland-inspired illustration.**

Rabbit Hole Archives is a text-first, AI-powered detective mystery game. Its interface should inspire curiosity and close observation while helping players reliably organize facts, question witnesses, inspect evidence, and develop theories. The visual system must support multiple cases, settings, and eras without asserting that every mystery takes place in one historical period.

**Three brand pillars**

1. **Atmosphere:** shadow, rainy streets, lamplight, restrained cinematic contrast, quiet tension.
2. **Materiality:** archived case files, evidence labels, typewritten records, rubber stamps, photographs, paper edges, and physical investigative ephemera.
3. **Character:** grounded, lightly storybook-inspired anthropomorphic rabbit illustrations, with expressive but credible characters.

**Design test:** Does the presentation make a clue more intriguing *and* easier to understand? If atmosphere interferes with reading or navigation, utility wins.

## 2. Approved direction and boundaries

Our approved visual direction blends the strongest elements of **classic noir** (mood and art direction) and **retro detective files** (materials and information architecture). Bunnyland's original illustrative sensibility informs approximately **10–25%** of the look, especially character rendering and small icon details; this is a *creative ratio*, not a measurable implementation requirement.

### Embrace
- Deep charcoal surfaces, muted paper, careful highlights, sparing plum and faded-crimson accents.
- Rain, reflections, smoky atmosphere, directed lighting, expressive silhouettes.
- Archive stamps, case markings, folders, labels, document stacks, filing tabs, photo evidence, investigation boards.
- Slightly painterly / ink-and-wash linework and stylized rabbit characters with believable posture, clothing, and emotional range.
- Strong editorial composition, legible typography, obvious navigation, spacious and consistent layouts.

### Avoid
- Overt Victorian / gothic-romantic decoration, ornate borders, heavy filigree, gilded flourishes as the default.
- Celestial motifs, crescent moons, astrology/compass-star decoration, pressed flowers, botanical ornaments.
- Excess whimsy, fantasy sparkle, twee / chibi faces, cartoon slapstick, or a consistently cozy tone.
- Generic SaaS dashboards or sterile forensic-software styling without personality.
- Grunge on body text, illegible faux-typewriter text, tiny metadata, visual noise, or decorative objects obscuring evidence.
- Committing the universal interface to one era. A *particular case* may have era-specific props, photographs, fashion, and documents.

**Note:** The approved moodboard still contains a few leftover botanical / celestial elements in its material collage and decorative marks. Those are **not** part of the approved design language. This written guide takes precedence when the reference image conflicts.

## 3. Brand voice and naming

**Working title:** Rabbit Hole Archives (omit “The”).

**Anchor line — preserve verbatim:**

> Some questions lead further down.

This line should be considered the lead tagline / brand phrase. It works on splash screens, title cards, store descriptions, and promotional artwork. It is not necessary to repeat it throughout routine gameplay UI.

Other exploratory copy, **not approved taglines**:
- Follow the clues beneath the surface.
- Different people. Hidden truths.
- Every file has another layer.

**Voice:** observant, confident, literary but concise, quietly intriguing, occasionally dry. The game should invite deduction without patronizing the player or explaining away every mystery.

## 4. Color system

The moodboard establishes **directional reference colors**, not final audited UI tokens. Approximate starting values taken from the approved concept:

| Token | Reference hex | Purpose |
|---|---|---|
| Midnight | `#0B0B0F` | Deepest background, title treatment |
| Charcoal | `#2A2A32` | Primary dark surfaces and panels |
| Fog gray | `#6B6F76` | Secondary visual structures, not small low-contrast text |
| Aged paper | `#D7C8AC` | Document surfaces, archive cards |
| Dusty violet | `#5B3F62` | Selected states and selective accent areas |
| Faded crimson | `#7A3B3B` | Archive stamps, important marks, sparing emphasis |

**Additional semantic colors will be required:** foreground text on both dark and light surfaces, borders, focus indicators, hover/pressed states, success/warning/error, and evidence provenance / confidence states. Do not adopt the moodboard's hex values blindly for small text or controls; tune them after contrast testing.

**Color rules**
- Let near-black, charcoal, and paper carry most of the interface.
- Choose one primary interactive accent and keep it consistent; dusty violet is the current candidate, pending contrast validation.
- Use crimson primarily as *visual archive language* (stamps, stamps of importance), never as the sole indicator of an error or suspicion.
- Pair colors with explicit text, shapes, or icons so meaning never depends on color alone.
- Maintain an accessible light-document mode within a dark application shell where appropriate.

## 5. Typography

**Hierarchy, not historical authenticity, is the priority.**

- **Display / branding:** expressive, high-contrast editorial serif for the game title, case titles, and large campaign art.
- **Reading / investigation narrative:** highly legible bookish serif or humanist sans; comfortable line height and paragraph width.
- **Navigation and data:** clean sans-serif for buttons, tabs, metadata, status labels, controls, and compact tables.
- **Typewriter / monospaced style:** selected evidence labels, dates, case numbers, archival annotations. Treat it as a documentary accent, not the default UI font.

Avoid all-caps tracking on long passages, decorative script for functional content, and artificial paper degradation over text. The type scale and font selection remain **open decisions**, to be validated in real screens.

## 6. Illustration, imagery, and Bunnyland influence

The preferred character treatment is **painterly, lightly stylized, semi-realistic anthropomorphic rabbits**: textured brushwork, softened naturalistic features, restrained outlines, plausible shadows, and believable material rendering. Noir lighting gives these figures gravity. The rabbit influence should be unmistakable but not overwhelming.

**Characters**
- Rabbit heads, ears, fur, expressive faces and gesture; grounded wardrobe, silhouettes and proportions.
- Detectives and suspects can appear in case-specific attire without forcing a permanent 1940s setting.
- Preserve a broad emotional range: guarded, tired, curious, angry, anxious, self-assured.
- Avoid making every character look friendly or comically suspicious.

**Environments and objects**
- Atmospheric location illustrations may use high-detail, cinematic lighting and gentle painterly edges.
- Evidence images must communicate the object clearly; neutral inspection views should be available apart from artistic hero images.
- Use distinct case-level visuals to convey time period and setting. The global UI language stays consistent.

**Rabbit motifs**
- A recognizable rabbit silhouette works for the logo, an archival case stamp, a navigation mark, and occasional decorative seals.
- Choose a small, repeatable icon family rather than embedding rabbits into every control.
- Bunnyland-inspired techniques should be most pronounced in characters and narrative illustration, not in tiny data-heavy UI components.

## 7. Material language and graphic motifs

**Approved motifs:** rubber stamps and distressed circular case marks (especially rabbit-head stamps); file folders and tabs; archival labels and evidence IDs; typed forms; documents and photographs; photo corners; paper clips; red string / visible connections; corkboard or dark investigation board; rain reflections and pools of lamplight.

**Rubber stamp design is a core motif.** Use it for case file covers, concept artwork, archival/administrative marks, and occasional transitions. Stamps should have imperfect ink impressions and slightly varied texture, but labels must remain decipherable. Do not turn every status badge into a stamp.

**Texture intensity by surface:**
- Brand and splash artwork: rich atmosphere and heavy texture permitted.
- Casebook headers and documents: subtle texture, kept away from long reading blocks.
- Routine buttons, form controls, tables, and body copy: nearly texture-free.

## 8. UI component direction

### A. Conversational Game Master
A dark, quiet, readable transcript takes precedence. Use illustrations as an anchor, not the entire backdrop of every conversation. The narrator should feel like a guide to the investigation, without replacing the player's judgment. Suggested actions are assistive, not mandatory; free-form input remains clearly available.

### B. Casebook / Archive
The core organizing metaphor: **an archive of open cases**. An active case has clear navigation for Overview, People, Evidence, Timeline, and Notes; Locations can be added when relevant. Folders/tabs can suggest the archive tactilely, but the structure should still behave like a predictable digital application.

### C. Suspect profiles
Use readable profile cards with consistent role, known facts, interview history, relationships, and links to evidence. Portrait art sets tone; factual details must be usable without the portrait. Avoid treating personality adjectives as objective guilt signals.

### D. Evidence / document viewer
Prioritize the *inspection task*: a large artifact preview, reliable zoom, selectable/transcribed text when possible, source / location / time acquired, and links back to the casebook. Decorative scuffs belong on the artifact image, not on the surrounding UI. Distinguish observed evidence from player annotation and AI narration.

### E. Timeline
A chronological, accessible view of reported and corroborated events. Show timestamps and confidence/provenance explicitly, including contradictions and unknown times. Purple lines and nodes may enhance the design but not replace semantic labels.

### F. Clue connection board (potential post-MVP feature)
Evoke the physical pin-and-string board, but support readable relationships, filtering, keyboard operation, and an alternate list/table view. Connections should be explainable rather than dependent on spatial position or string color alone.

## 9. Interaction and accessibility principles

Accessibility is a *release requirement*, not a finishing touch.

- Target **WCAG 2.2 AA** for implemented web UI, where applicable.
- Test text contrast (generally 4.5:1 for normal text; 3:1 for large text) and non-text control indicators (generally 3:1).
- Ensure complete keyboard navigation, logical focus order, visible focus states, and appropriate control labels.
- Respect reduced-motion preferences; avoid flashing noir light effects.
- Offer a text/list alternative for purely visual clue graphs.
- Support text scaling and responsive layouts without forcing reading inside tiny fixed cards.
- Do not convey certainty, case status, time sequence, or relationships by color, texture, or icon alone.
- Decorative weather, shadows, handwriting, and paper aging must never lower the readability of the case data.

## 10. Era-flexibility rules

The **application shell** carries the Rabbit Hole Archives brand: its typography system, spacing, navigation, tabs, buttons, and interaction patterns remain stable across cases.

**Individual case content** may have changing: period costumes, investigative technology, document templates, location illustration styles, photography, audio, typography *within artifacts*, and narrative tone. For example, a 1950s hotel mystery could contain typewritten interview notes while a contemporary case could contain emails or digital logs; both are inspected in the same accessible evidence viewer.

This prevents universal branding from accidentally becoming a promise that every case is a vintage noir mystery.

## 11. Logo and identity exploration

Three approved **exploration families** from the moodboard (not final logo selections):

1. **Rabbit / skyline silhouette:** cinematic, expressive, suitable for title cards.
2. **Archival file stamp / dossier label:** strongest link to the casebook and evidence system.
3. **Minimal rabbit roundel:** compact icon candidate for favicon, app mark, and stamps.

For a future production logo, test full wordmark, horizontal layout, square icon, single-color version, and small-size legibility. Avoid ornate lines that collapse at favicon size. Final wordmark design and logo artwork remain undecided.

## 12. Generation brief for future concept art

Reusable direction:

> **Rabbit Hole Archives** — cinematic noir and tactile archival detective-file aesthetic. Serious, curious, quietly atmospheric; rain-soaked urban lighting, shadow and lamplight, worn case folders, typed records, photographs, rubber stamps with distressed rabbit-head emblems, subtle dusty-plum and faded-crimson accents. Include restrained Bunnyland-inspired painterly, semi-realistic anthropomorphic rabbit character illustration (approximately 10–25% of the visual style), never overtly cute. Favor a charcoal / fog-gray / aged-paper palette, premium editorial typography, legible information hierarchy, and restrained composition. Keep the core game aesthetic flexible across settings and eras. **Exclude celestial and botanical motifs, Victorian romantic ornament, fantasy sparkles, generic SaaS styling, and cluttered evidence displays.**

When generating *interface explorations*, further specify that they are **static concepts, not functioning designs**, and request clear controls, realistic content density, and distinct readable panels. Verify layouts and text independently before implementation.

## 13. Design QA checklist

Before accepting a new visual asset or UI concept, ask:

- [ ] Does it feel investigative and atmospheric instead of cozy fantasy or generic enterprise UI?
- [ ] Does it match the noir + archive visual system?
- [ ] Is Bunnyland influence present but secondary?
- [ ] Have romantic/Victorian flourishes, celestial marks, and botanical ornaments been avoided?
- [ ] Is the text readable without zooming or deciphering distressed typography?
- [ ] Does the most important action or evidence stand out clearly?
- [ ] Are interactive states and meanings communicated beyond color alone?
- [ ] Would this universal UI still work in a case set in a different era?
- [ ] Is decorative texture restrained where evidence must be read?
- [ ] Is this clearly a concept image, rather than being mistaken for an implementation spec?

## 14. Decisions still open

- Final logo and whether rabbit iconography is used in the main wordmark.
- Production typefaces and specific text-size/spacing scale.
- Final audited design tokens, including semantic color and accessible accent variants.
- How much character illustration appears in routine GM conversations.
- Whether the default global shell is dark-only or supports a light theme.
- Design system/component implementation strategy and responsive breakpoints.
- Whether the clue connection board belongs in the MVP.

**Source of truth:** This document records the current agreed creative direction. The accompanying approved moodboard demonstrates the look; for conflicts—especially leftover decorative celestial or botanical details—follow this guide rather than the image.