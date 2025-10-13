# Quick Start Guide

## Getting Started with Your Portfolio

### 1. Personalize Your Content

Open `index.html` and update the following:

#### Hero Section (Lines ~90-100)
```html
<h1 class="gradient-name">Antoine BINNER</h1>
<p class="about-me-tagline">
    2nd Year Electronic Engineering Student<br>
    Your custom tagline here...
</p>
```

#### Contact Links (Lines ~300+)
Update your email, LinkedIn, and GitHub URLs.

### 2. Add Your Projects

Each section has example project cards. To add more:

1. Copy an existing `.experience-card` div
2. Update the content:
   - Project title
   - Date
   - Description
   - Image or icon

Example:
```html
<div class="experience-card">
    <div class="experience-info">
        <h2 class="experience-brand">Your Project Name</h2>
        <div class="experience-image">
            <i class="fas fa-microchip fa-5x" style="color: #667eea;"></i>
        </div>
        <p class="experience-date"><em>Date</em></p>
        <p class="experience-description">
            Project description here...
        </p>
    </div>
    <button class="card-btn">Learn More</button>
</div>
```

### 3. Add Your Photo

Replace the placeholder icon with your photo:

1. Add your photo to the `images/` folder (e.g., `profile.jpg`)
2. In `index.html`, replace:

```html
<!-- Remove this: -->
<div class="headshot-placeholder">
  <i class="fas fa-user fa-5x"></i>
</div>

<!-- Add this: -->
<img src="images/profile.jpg" alt="Antoine BINNER" class="headshot">
```

### 4. Update Skills

Modify the skills section to match your abilities:
- Technical Skills
- Programming Languages
- Tools and Frameworks

### 5. Test Locally

Open `index.html` in your web browser to preview your site.

### 6. Deploy to GitHub Pages

Follow the instructions in `README.md` to deploy your site.

## Need Help?

- Check the full README.md for detailed instructions
- All sections are clearly commented in the HTML
- CSS files are organized by component

## Tips

1. **Icons**: This template uses Font Awesome icons. Browse available icons at https://fontawesome.com/icons
2. **Colors**: To change colors, search for `#667eea` and `#764ba2` in CSS files
3. **Fonts**: Current fonts are Montserrat (headings) and Poppins (body text)
4. **Mobile**: The site is fully responsive - test on different screen sizes!

Good luck with your portfolio! 🚀
