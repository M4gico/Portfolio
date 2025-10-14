# Theme Color Locations - Complete Guide

## Main Theme Color Locations in the Code

### 1. **CSS Variables (Root Configuration)**
**Location:** `css/style.css` - Lines 6-10

```css
:root {
  --theme-primary: #667eea;
  --theme-secondary: #764ba2;
  --theme-accent: #8b5cf6;
}
```

**Purpose:** Global CSS variables that can be referenced throughout the stylesheets
**Default Theme:** Purple Indigo

---

### 2. **Body Background Gradient**
**Location:** `css/style.css` - Line 20

```css
body {
  font-family: 'Poppins', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  line-height: 1.6;
  overflow-x: hidden;
}
```

**Purpose:** Main background gradient for the entire website
**Colors:** 
- Start: `#667eea` (Soft Purple)
- End: `#764ba2` (Deep Indigo)

---

### 3. **JavaScript Theme Configurations**
**Location:** `js/theme_switcher.js` - Lines 7-45

```javascript
const themes = {
  'purple-indigo': {
    name: 'Purple Indigo',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    primary: '#667eea',
    secondary: '#764ba2',
    accent: '#8b5cf6'
  },
  'blue-cyan': {
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    primary: '#4facfe',
    secondary: '#00f2fe',
    accent: '#06b6d4'
  },
  'green-teal': {
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    primary: '#43e97b',
    secondary: '#38f9d7',
    accent: '#10b981'
  },
  'orange-red': {
    gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    primary: '#fa709a',
    secondary: '#fee140',
    accent: '#f97316'
  },
  'dark-blue': {
    gradient: 'linear-gradient(135deg, #2c3e50 0%, #3498db 100%)',
    primary: '#2c3e50',
    secondary: '#3498db',
    accent: '#2563eb'
  }
};
```

**Purpose:** Theme switcher configurations for all 5 available themes

---

### 4. **Button Gradient**
**Location:** `css/style.css` - Line 66

```css
.card-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  /* ... */
}
```

**Purpose:** "Learn More" button gradient
**Colors:** Same as body background

---

### 5. **Name Color (Main Title)**
**Location:** `css/head.css` - Line 60

```css
.gradient-name {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 1rem;
  font-family: 'Montserrat', sans-serif;
  color: #667eea;
  letter-spacing: 3px;
}
```

**Purpose:** Your name color on the homepage
**Color:** `#667eea` (Primary purple)

---

### 6. **Progress Bar**
**Location:** `css/scroll_progress.css` (assumed)

The progress bar color is dynamically set by the theme switcher:
```javascript
progressBar.style.background = theme.gradient;
```

---

### 7. **Section Backgrounds (Alternating)**
**Location:** `css/style.css` - Lines 53-61

```css
.section-darker {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
}

.section-lighter {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
}
```

**Purpose:** Alternating section backgrounds (not theme-colored, but used for separation)

---

### 8. **Navigation Hover Effects**
**Location:** Dynamically applied by JavaScript in `js/theme_switcher.js`

When theme changes, navigation links get hover colors:
```javascript
navLinks.forEach(link => {
  link.addEventListener('mouseenter', function() {
    this.style.color = theme.primary;
  });
});
```

---

### 9. **Personal Projects Page**
**Location:** `personal-projects.html` - Lines 26-30

```css
:root {
  --theme-primary: #2c3e50;
  --theme-secondary: #3498db;
  --theme-accent: #2563eb;
}
```

**Note:** This page starts with dark-blue theme variables but can be changed by theme switcher

---

## How to Change the Default Theme Color

### Option 1: Change CSS Variables (Quick Change)
**File:** `css/style.css`

Change lines 6-10:
```css
:root {
  --theme-primary: #YOUR_PRIMARY_COLOR;
  --theme-secondary: #YOUR_SECONDARY_COLOR;
  --theme-accent: #YOUR_ACCENT_COLOR;
}
```

### Option 2: Change Body Background (Main Background)
**File:** `css/style.css`

Change line 20:
```css
body {
  background: linear-gradient(135deg, #COLOR1 0%, #COLOR2 100%);
}
```

### Option 3: Change Default Theme in JavaScript
**File:** `js/theme_switcher.js`

Modify the `purple-indigo` theme object (lines 8-13) or change the default load theme at line 135.

### Option 4: Change Button Colors
**File:** `css/style.css`

Change line 66:
```css
.card-btn {
  background: linear-gradient(135deg, #COLOR1 0%, #COLOR2 100%);
}
```

---

## Current Active Theme: Dark Blue

### Current Colors in Use:
- **Primary:** `#2c3e50` (Dark Slate)
- **Secondary:** `#3498db` (Professional Blue) - with 55% lightness adjustment
- **Accent:** `#2563eb` (Royal Blue)
- **Gradient:** `linear-gradient(135deg, #2c3e50 0%, #3498db 100%)`

### Where It's Applied:
1. Body background
2. All buttons
3. Progress bar
4. CSS variables
5. Name color adapts to theme

---

## Dynamic Theme Changes

The theme switcher (`js/theme_switcher.js`) handles dynamic color changes:

**Function:** `changeTheme(themeName)` - Line 58

This function updates:
- Body background
- All button gradients
- Name color
- Progress bar
- CSS variables
- Navigation hover colors

**Storage:** Theme preference saved in `localStorage.selectedTheme`

---

## Color Adjuster for Dark Blue Theme

**Location:** `js/theme_switcher.js` - Line 177

Function `getAdjustedBlueColor(lightness)` allows you to adjust the blue theme lightness:
```javascript
function getAdjustedBlueColor(lightness) {
  return `hsl(204, 70%, ${lightness}%)`;
}
```

**Current Default Lightness:** 55%

---

## Summary Table

| Element | File | Line(s) | Default Color |
|---------|------|---------|---------------|
| CSS Variables | `css/style.css` | 6-10 | #667eea, #764ba2 |
| Body Background | `css/style.css` | 20 | Gradient Purple-Indigo |
| Button Background | `css/style.css` | 66 | Gradient Purple-Indigo |
| Name Color | `css/head.css` | 60 | #667eea |
| Theme Configs | `js/theme_switcher.js` | 7-45 | 5 theme objects |
| Section Backgrounds | `css/style.css` | 53-61 | Black/White overlays |

---

## Notes

1. **Theme Persistence:** Selected theme is saved to browser's localStorage
2. **Dynamic Updates:** Theme switcher updates all elements in real-time
3. **Lightness Adjuster:** Only works with dark-blue theme (HSL color manipulation)
4. **Priority:** Inline styles with `!important` override theme (e.g., Unity logo)
5. **Fallback:** If no theme selected, defaults to purple-indigo theme (current: dark-blue)
