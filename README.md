# Antoine BINNER - Electronic Engineering Portfolio

Welcome to my portfolio website! This site showcases my academic projects, personal projects, and internship experience.

## 🚀 Features

- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Modern UI**: Gradient animations and smooth transitions
- **Three Main Sections**:
  - Academic Projects
  - Personal Projects
  - Internship Experience
- **Interactive Navigation**: Smooth scrolling and mobile-friendly hamburger menu
- **Scroll Progress Bar**: Visual indicator of page scroll progress
- **Project Carousels**: Easy navigation through project cards

## 📁 Project Structure

```
portfolio/
│
├── index.html              # Main HTML file
├── README.md              # This file
│
├── css/                   # Stylesheets
│   ├── style.css         # Global styles
│   ├── nav.css           # Navigation styles
│   ├── head.css          # Hero section styles
│   ├── experience.css    # Project cards styles
│   ├── contact.css       # Contact section styles
│   ├── footer.css        # Footer styles
│   └── scroll_progress.css # Scroll bar styles
│
├── js/                    # JavaScript files
│   ├── script.js         # Main functionality
│   └── scroll_progress.js # Scroll progress bar
│
└── images/               # Images folder (optional)
    └── arrow.png         # Navigation arrows
```

## 🛠️ Customization

### 1. Personal Information

Edit `index.html` to update:
- Your name in the hero section
- Your tagline/description
- Email, LinkedIn, and GitHub links in the contact section

### 2. Skills

Update the skills section with your own technical skills, programming languages, and tools.

### 3. Projects

Add your own projects by duplicating the `.experience-card` divs in each section:
- Academic Projects
- Personal Projects
- Internship Experience

### 4. Profile Picture

Replace the icon placeholder with your own image:
```html
<!-- Replace this: -->
<div class="headshot-placeholder">
  <i class="fas fa-user fa-5x"></i>
</div>

<!-- With this: -->
<img src="images/your-photo.jpg" alt="Antoine BINNER" class="headshot">
```

### 5. Project Images

Add images to your project cards:
```html
<div class="experience-image">
  <img src="images/project-name.jpg" class="experience-thumb" alt="Project Name">
</div>
```

### 6. Colors

To change the color scheme, update the gradient colors in CSS files:
- Primary gradient: `#667eea` and `#764ba2`
- Find and replace these hex codes throughout the CSS files

## 🌐 Deploying to GitHub Pages

### Step 1: Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the '+' icon in the top right and select 'New repository'
3. Name it: `your-username.github.io` (replace `your-username` with your GitHub username)
4. Make it public
5. Don't initialize with README (you already have one)
6. Click 'Create repository'

### Step 2: Upload Your Files

**Option A: Using Git (Recommended)**

```bash
# Navigate to your project folder
cd d:\Code\Web

# Initialize git repository
git init

# Add all files
git add .

# Commit changes
git commit -m "Initial portfolio commit"

# Add your GitHub repository as remote
git remote add origin https://github.com/your-username/your-username.github.io.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Option B: Using GitHub Web Interface**

1. On your repository page, click 'uploading an existing file'
2. Drag and drop all your files
3. Click 'Commit changes'

### Step 3: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click 'Settings'
3. Scroll down to 'Pages' in the left sidebar
4. Under 'Source', select 'main' branch
5. Click 'Save'
6. Wait a few minutes for deployment

### Step 4: Access Your Site

Your site will be available at: `https://your-username.github.io`

## 📝 Tips for GitHub Pages

1. **Custom Domain**: You can add a custom domain in the GitHub Pages settings
2. **Updates**: Any changes pushed to the main branch will automatically update your site
3. **HTTPS**: GitHub Pages automatically provides HTTPS for your site
4. **SEO**: Update the meta tags in `index.html` with your actual URLs

## 🎨 Browser Compatibility

This portfolio is compatible with:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## 📧 Contact

If you have questions or suggestions, feel free to reach out!

- Email: your.email@example.com
- LinkedIn: [Your Profile](https://www.linkedin.com/in/your-profile)
- GitHub: [Your Username](https://github.com/your-username)

## 📄 License

Feel free to use this template for your own portfolio! Attribution is appreciated but not required.

---

**Built with HTML, CSS, and JavaScript**

© 2025 Antoine BINNER
