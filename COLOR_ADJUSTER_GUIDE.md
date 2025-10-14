# Dark Blue Theme Color Adjuster Guide

## Overview
The Dark Blue theme now has an interactive color adjuster that allows you to fine-tune the blue lightness to your preference.

---

## How to Use

1. **Open Theme Menu**
   - Click the palette icon (🎨) in the bottom-right corner

2. **Access Color Adjuster**
   - Click "Adjust Colors" at the bottom of the theme menu

3. **Adjust the Slider**
   - Move the slider left for **darker blue** (20% - 50%)
   - Move the slider right for **lighter blue** (50% - 80%)
   - Current value is displayed next to "Blue Lightness"
   - Live preview shows the gradient result

4. **Apply Changes**
   - Click "Apply" to use the new color scheme
   - Click "Reset" to return to default (50%)
   - Click "✕" to close without applying

---

## Slider Range

| Value | Description | Use Case |
|-------|-------------|----------|
| 20-30% | Very Dark | Minimal, professional, night mode |
| 30-40% | Dark | Professional, focused work |
| 40-50% | Medium-Dark | Balanced (default region) |
| 50-60% | Medium | Clear visibility |
| 60-70% | Light | Bright, energetic |
| 70-80% | Very Light | High contrast, day mode |

---

## Default Values
- **Default Lightness:** 50%
- **Base Color:** `hsl(204, 70%, 50%)` → `#3498db`
- **Adjusted Range:** `hsl(204, 70%, 20-80%)`

---

## Technical Details

### Color Calculation
- **Hue:** 204° (Blue) - Fixed
- **Saturation:** 70% - Fixed
- **Lightness:** Adjustable (20% - 80%)

### What Gets Updated
- ✅ Body background gradient
- ✅ Button backgrounds
- ✅ Name color
- ✅ Progress bar
- ✅ CSS variables

### Persistence
- Your chosen lightness value is saved in browser localStorage
- Theme persists across page refreshes
- Each browser/device stores its own preference

---

## Example Values to Try

### Professional & Subtle
**Value:** 35%
- Very dark, professional look
- Great for focused work sessions

### Balanced (Default)
**Value:** 50%
- Original dark blue theme
- Good all-around visibility

### Bright & Clear
**Value:** 65%
- Lighter, more visible
- Better for well-lit environments

---

## Instructions for Selecting Your Preferred Value

1. Open the color adjuster
2. Try different slider positions
3. Check how it looks with your content
4. **Note the value you prefer** (shown next to the slider)
5. Share that value if you want to set it as the permanent default

**Example:** "I like 42%" or "Set it to 58%"

---

## Console Logging
When you apply a value, check the browser console (F12) to see:
```
✅ Applied custom dark-blue theme with lightness: XX%
Primary: hsl(210, 30%, XX%)
Secondary: hsl(204, 70%, XX%)
Accent: hsl(204, 70%, XX%)
```

This helps with debugging and knowing exact color values being applied.
