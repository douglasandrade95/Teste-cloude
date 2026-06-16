---
name: logo-carousel
description: Create and manage animated logo carousels for displaying client logos, partner logos, or any image carousel. Use when asked to build a carousel component, create a logo slider, set up image rotation, or generate carousel code.
---

# Logo Carousel Skill

This skill helps you create animated logo carousels using React. The carousel automatically shuffles logos and displays them in a continuous scrolling animation.

## Basic Usage

To create a logo carousel component, you need:

1. **Client/Logo Data** - An array of objects with the following structure:
```javascript
const clients = [
  {
    name: "Company Name",
    description: "Brief description",
    url: "https://company.com",
    lightSrc: "/images/logos/company/logo-light.svg",
    darkSrc: "/images/logos/company/logo-dark.svg",
    scale: 1, // Optional: scale factor (default 1)
    instructionsUrl: "https://company.com/docs",
    sourceCodeUrl: "https://github.com/company/repo"
  },
  // ... more clients
];
```

2. **React Component** - Use this carousel component:
```javascript
import React, { useState, useEffect } from 'react';

export const LogoCarousel = ({clients}) => {
  const [shuffled, setShuffled] = useState(clients);
  
  useEffect(() => {
    const shuffle = items => {
      const copy = [...items];
      for (let i = copy.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [copy[i], copy[j]] = [copy[j], copy[i]];
      }
      return copy;
    };
    setShuffled(shuffle(clients));
  }, []);
  
  const doubled = [...shuffled, ...shuffled];
  const GAP_PX = 48;
  const PX_PER_SECOND = 40;
  const cycleWidth = shuffled.reduce((sum, client) => sum + 150 * (client.scale || 1) + GAP_PX, 0);
  const cycleDuration = cycleWidth / PX_PER_SECOND;
  
  const Logo = ({client}) => (
    <a href={client.url} className="block no-underline border-none w-full h-full">
      <img className="block dark:hidden object-contain w-full h-full !my-0" 
           src={client.lightSrc} alt={client.name} noZoom />
      <img className="hidden dark:block object-contain w-full h-full !my-0" 
           src={client.darkSrc} alt={client.name} noZoom />
    </a>
  );
  
  return (
    <div className="logo-carousel">
      <div className="logo-carousel-track" style={{
        animation: `logo-scroll ${cycleDuration}s linear infinite`
      }}>
        {doubled.map((client, i) => (
          <div key={`${client.name}-${i}`} style={{
            width: 150 * (client.scale || 1),
            maxWidth: "100%"
          }}>
            <Logo client={client} />
          </div>
        ))}
      </div>
    </div>
  );
};
```

3. **CSS Styles** - Add the animation and styling:
```css
.logo-carousel {
  width: 100%;
  overflow: hidden;
  background: transparent;
}

.logo-carousel-track {
  display: flex;
  gap: 48px;
  padding: 24px 0;
  will-change: transform;
}

@keyframes logo-scroll {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-50%);
  }
}

.logo-carousel a {
  transition: opacity 0.3s ease;
}

.logo-carousel a:hover {
  opacity: 0.8;
}
```

## Customization

### Adjust Animation Speed
Change `PX_PER_SECOND` in the component (40 is the default):
- Lower values = slower scroll
- Higher values = faster scroll

### Adjust Gap Between Logos
Change `GAP_PX` (48 is the default):
- Larger values = more space between logos
- Smaller values = tighter spacing

### Scale Specific Logos
Add `scale` property to client objects:
```javascript
{
  name: "Small Company",
  scale: 0.8, // Will be 80% of standard width
  // ... other properties
}
```

## Dark Mode Support

The carousel automatically supports dark mode by displaying different logos based on the `.dark` class:
- Light mode: displays `lightSrc` image
- Dark mode: displays `darkSrc` image

## Features

✓ Automatic logo shuffling on load
✓ Infinite continuous scrolling animation
✓ Responsive and mobile-friendly
✓ Dark mode support with separate logos
✓ Clickable logos linking to company URLs
✓ Configurable speed and spacing
✓ Optional per-logo scaling

## Performance Notes

- The carousel uses CSS animations for smooth 60fps scrolling
- No JavaScript animation loop needed
- Doubles the logo array to create seamless looping
- Efficient with will-change CSS optimization
