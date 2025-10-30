# Anime Art Generation Prompts for Landing Page

## Main Room Background (Top-Down View)

### Master Prompt for Room Background

```
A cozy anime-style developer's bedroom in top-down isometric view, chibi art style, pastel colors, kawaii aesthetic. The room should show:

LAYOUT:
- Rectangular room with visible floor (light wood or tatami mat pattern)
- Walls visible on two sides (creating depth)
- Window on one wall with soft sunlight streaming in
- Door slightly ajar on another wall

FURNITURE PLACEMENT (for widget overlay):
- TOP LEFT: Large analog wall clock area (empty space reserved)
- TOP CENTER: Window with curtains, small potted cactus on windowsill
- TOP RIGHT: Corner bookshelf (tall, 4-5 shelves, some books visible)
- MIDDLE LEFT: Desk area with papers scattered (clear space for widget)
- MIDDLE CENTER: Empty floor space with soft rug
- MIDDLE RIGHT: Small table with microwave/display device
- BOTTOM LEFT: Filing cabinet or storage drawers
- BOTTOM CENTER: Smartphone on a charging mat on floor
- BOTTOM RIGHT: Small plant in decorative pot

STYLE:
- Soft pastel color palette: pink, lavender, mint green, peach, sky blue
- Chibi anime art style with clean lines
- Warm, inviting atmosphere
- Soft shadows and gentle lighting
- Slightly messy but organized (lived-in feel)
- Japanese/kawaii aesthetic elements
- NO character in the scene (furniture and items only)

TECHNICAL:
- High resolution (2000x1500px minimum)
- PNG with transparency where needed
- Soft gradients for lighting
- Clear spaces reserved for interactive widgets to overlay
- Isometric perspective at 30-degree angle
- Pastels: #FFB3D9 (pink), #E6D5F5 (purple), #B8E6FF (blue), #B4F5D0 (mint), #FFF5BA (yellow)

MOOD: Peaceful, cozy, organized chaos, developer's sanctuary, kawaii energy
```

## Individual Widget Background Images

### 1. Clock Widget (⏰)
```
Large round analog wall clock in anime chibi style, kawaii aesthetic, pastel pink frame with white face, cute numbers, decorative clock hands with heart-shaped tips, soft glow around edges, transparent PNG background, 400x400px, top-down slight angle view
```

### 2. Version Display Widget (🖥️)
```
Cute microwave or digital display device in anime chibi style, pastel purple/blue casing, small LED display screen showing version numbers, kawaii design with rounded edges, small decorative buttons, soft glow from screen, transparent PNG, 300x300px, top-down view
```

### 3. Uptime Plant Widget (🌱)
```
Three growth stages of a cute anime cactus in decorative pot:
Stage 1 (small): Tiny cactus with 2-3 spikes, happy face, small pink flower bud
Stage 2 (medium): Larger cactus with more spikes, blooming pink flower
Stage 3 (large): Full grown cactus with multiple pink flowers, very happy expression
Kawaii style, pastel green cactus, peach/pink pot with heart pattern, transparent PNG, 250x250px each
```

### 4. Redis Status - Desk Widget (📄)
```
Two versions of a cute anime-style desk top view:
Version A (Clean/Online): Organized papers in neat stacks, colorful sticky notes, cute pen holder, small coffee cup, soft glow indicating "all good"
Version B (Messy/Offline): Scattered papers, overturned coffee cup (no spill, just tilted), disorganized, warning signs
Chibi art style, pastel colors, transparent PNG, 600x300px, top-down view
```

### 5. PostgreSQL - Bookshelf Widget (📚)
```
Corner bookshelf in anime chibi style, 4 shelves visible, colorful book spines (pastel pink, blue, green, purple), some books glowing softly (active queries), decorative items between books (small figures, plants), wooden shelf with kawaii details, transparent PNG, 400x400px, isometric corner view
```

### 6. Bot Status - Smartphone Widget (📱)
```
Modern smartphone on a cute charging mat in anime chibi style, screen glowing with notification light, small heart-shaped glow pulse, pastel pink/blue gradient on screen, kawaii decorative case with stickers, transparent PNG, 250x250px, top-down view
```

### 7. GitHub Actions - Robot Vacuum Widget (🤖)
```
Cute round robot vacuum cleaner in anime chibi style, happy face on top, small wheels, pastel blue/white color scheme, soft glow lights, optional motion lines when active, kawaii stickers on body, transparent PNG, 200x200px, top-down view
```

### 8. Changelog Widgets

#### v0.1.0 - Plushie (🧸)
```
Cute anime plushie of Lilith (orange-red wavy hair chibi character) sitting/lying on bed, soft pastel colors, kawaii face expression, small and huggable, transparent PNG, 200x200px
```

#### v0.0.9-canary - Canary Bird (🐤)
```
Adorable yellow canary bird in a cute decorative cage, anime chibi style, bird singing happily, pastel yellow/gold colors, small cage with kawaii details, transparent PNG, 200x200px
```

#### Initial - Seed Packet (🌱)
```
Decorative seed packet in anime style, colorful illustration on front, "Lilith Seeds" branding, cute mascot on package, pastel colors, slightly open with seeds visible, transparent PNG, 200x200px
```

### 9. The Edge Story Ad Widget (📰)
```
Retro 90s anime poster style advertisement, "The Edge Story" title in bold katakana-style font, cyberpunk meets kawaii aesthetic, pastel pink/purple/blue gradient, small decorative elements (stars, sparkles), transparent PNG, 300x500px, portrait orientation
```

### 10. GameBoy Placeholder (🎮)
```
Classic Game Boy handheld console in anime chibi style, pastel pink/purple color scheme, screen showing simple pixel art (Pong game), cute stickers on body, kawaii design, transparent PNG, 250x300px, slight angle view
```

### 11. Cactus Decorative (🌵)
```
Simple cute cactus in round pot, anime chibi style with happy face, small pink flowers, pastel green body, peach pot with polka dots, transparent PNG, 150x150px
```

### 12. Photo Frame - Admins (🖼️)
```
Decorative photo frame in anime style, "2 Admins ♥" text visible, heart decorations around frame, pastel pink/gold colors, kawaii ornate design, transparent PNG, 200x200px
```

### 13. Bulletin Board - Memories (📌)
```
Cork bulletin board with colorful sticky notes, pins, and reminders, anime chibi style, pastel colored notes (pink, yellow, blue, green), some notes with small drawings, kawaii pushpins, transparent PNG, 400x300px
```

### 14. Filing Cabinet - RAG System (🗄️)
```
Small filing cabinet with open drawer showing abstract glowing "embeddings" (colorful floating orbs/particles), anime chibi style, pastel gray cabinet, magical glow from drawer, kawaii labels, transparent PNG, 300x400px
```

## Generation Guidelines

**Style Consistency:**
- All images should use the same chibi anime art style
- Consistent pastel color palette across all assets
- Similar line thickness and shading techniques
- Kawaii elements (hearts, stars, sparkles) used sparingly

**Technical Requirements:**
- All images PNG with transparency
- High resolution (2x size for retina displays)
- Optimized file sizes (< 100KB per image)
- Consistent lighting direction (top-left)

**Integration Plan:**
1. Generate main room background first
2. Generate widget images in priority order (clock, version, status first)
3. Test each image in layout before generating next batch
4. Iterate on prompts based on results

## AI Generation Tools to Use

**Recommended:**
- Stable Diffusion (local or cloud)
- Midjourney (for high-quality anime style)
- DALL-E 3 (for quick iterations)
- NovelAI (specialized in anime)

**Prompt Enhancements:**
- Add "high quality, detailed, professional" for better results
- Add "no watermark, no text" to avoid unwanted elements
- Use negative prompts: "realistic, photograph, 3D render, blurry"
