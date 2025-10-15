// Theme Switcher Functionality

// Current lightness value for dark-blue theme
let currentLightness = 55;

// Theme configurations with electronics/student/work vibe
const themes = {
  'purple-indigo': {
    name: 'Purple Indigo',
    description: 'Professional & Creative - Default electronics theme',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    primary: '#667eea',
    secondary: '#764ba2',
    accent: '#8b5cf6'
  },
  'blue-cyan': {
    name: 'Blue Cyan',
    description: 'Tech & Innovation - Circuit board inspired',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    primary: '#4facfe',
    secondary: '#00f2fe',
    accent: '#06b6d4'
  },
  'green-teal': {
    name: 'Green Teal',
    description: 'Energy & Growth - PCB green aesthetic',
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    primary: '#43e97b',
    secondary: '#38f9d7',
    accent: '#10b981'
  },
  'orange-red': {
    name: 'Orange Sunset',
    description: 'Dynamic & Energetic - Soldering iron warmth',
    gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    primary: '#fa709a',
    secondary: '#fee140',
    accent: '#f97316'
  },
  'dark-blue': {
    name: 'Dark Blue',
    description: 'Professional & Focused - Laboratory precision',
    gradient: 'linear-gradient(135deg, hsl(210, 30%, 35%) 0%, hsl(204, 70%, 55%) 100%)',
    primary: 'hsl(210, 30%, 35%)',
    secondary: 'hsl(204, 70%, 55%)',
    accent: 'hsl(204, 70%, 65%)'
  }
};

// Toggle theme menu visibility
function toggleThemeMenu() {
  const menu = document.getElementById('themeMenu');
  menu.classList.toggle('show');
}

// Close theme menu when clicking outside
document.addEventListener('click', function(event) {
  const menu = document.getElementById('themeMenu');
  const button = document.querySelector('.theme-switcher');
  
  if (!menu.contains(event.target) && !button.contains(event.target)) {
    menu.classList.remove('show');
  }
});

// Change theme
function changeTheme(themeName) {
  const theme = themes[themeName];
  
  if (!theme) {
    console.error('Theme not found:', themeName);
    return;
  }
  
  // Update body background gradient
  document.body.style.background = theme.gradient;
  
  // Update all gradient buttons
  const buttons = document.querySelectorAll('.card-btn');
  buttons.forEach(btn => {
    btn.style.background = theme.gradient;
  });
  
  // Update name color
  const nameElements = document.querySelectorAll('.gradient-name');
  nameElements.forEach(el => {
    el.style.color = theme.secondary;
    el.style.textShadow = `2px 2px 4px ${theme.secondary}4D`; // 30% opacity
  });
  
  // Update navigation hover effects
  const navLinks = document.querySelectorAll('nav a');
  navLinks.forEach(link => {
    link.addEventListener('mouseenter', function() {
      this.style.color = theme.primary;
    });
    link.addEventListener('mouseleave', function() {
      this.style.color = '#ffffff';
    });
  });
  
  // Update progress bar
  const progressBar = document.getElementById('myBar');
  if (progressBar) {
    progressBar.style.background = theme.gradient;
  }
  
  // Update button hover effects (via CSS variable)
  document.documentElement.style.setProperty('--theme-primary', theme.primary);
  document.documentElement.style.setProperty('--theme-secondary', theme.secondary);
  document.documentElement.style.setProperty('--theme-accent', theme.accent);
  
  // Save theme preference to localStorage
  localStorage.setItem('selectedTheme', themeName);
  
  // Close menu
  toggleThemeMenu();
  
  console.log(`Theme changed to: ${theme.name}`);
}

// Load saved theme on page load
window.addEventListener('DOMContentLoaded', function() {
  const savedTheme = localStorage.getItem('selectedTheme');
  const savedLightness = localStorage.getItem('darkBlueLightness');
  
  if (savedLightness) {
    currentLightness = parseInt(savedLightness);
  } else {
    currentLightness = 55;
  }
  
  // Update slider to show current value
  const slider = document.getElementById('lightnessSlider');
  const valueDisplay = document.getElementById('lightnessValue');
  if (slider && valueDisplay) {
    slider.value = currentLightness;
    valueDisplay.textContent = currentLightness + '%';
  }
  
  if (savedTheme && themes[savedTheme]) {
    changeTheme(savedTheme);
  } else {
    // Set default theme to dark-blue
    // Apply with saved or default lightness only if user had previously customized it
    if (savedLightness) {
      changeTheme('dark-blue');
      setTimeout(() => applyLightness(), 100);
    } else {
      // First time load - use standard dark-blue theme
      changeTheme('dark-blue');
    }
  }
});

// Helper function to convert hex to HSL
function hexToHSL(hex) {
  // Remove the # if present
  hex = hex.replace('#', '');
  
  // Convert hex to RGB
  let r = parseInt(hex.substring(0, 2), 16) / 255;
  let g = parseInt(hex.substring(2, 4), 16) / 255;
  let b = parseInt(hex.substring(4, 6), 16) / 255;
  
  let max = Math.max(r, g, b);
  let min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;
  
  if (max === min) {
    h = s = 0; // achromatic
  } else {
    let d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  
  return {
    h: Math.round(h * 360),
    s: Math.round(s * 100),
    l: Math.round(l * 100)
  };
}

// Helper function to create adjusted color based on lightness
function getAdjustedBlueColor(lightness) {
  // Base color is #3498db (HSL: 204, 70%, 53%)
  // We'll adjust the lightness while keeping hue and saturation
  return `hsl(204, 70%, ${lightness}%)`;
}

// Open color adjuster panel
function openColorAdjuster() {
  document.getElementById('themeMenu').classList.remove('show');
  document.getElementById('colorAdjuster').classList.add('show');
  updateLightness(currentLightness);
}

// Close color adjuster panel
function closeColorAdjuster() {
  document.getElementById('colorAdjuster').classList.remove('show');
}

// Update lightness value and preview
function updateLightness(value) {
  currentLightness = parseInt(value);
  document.getElementById('lightnessValue').textContent = currentLightness + '%';
  
  // Update preview
  const color = getAdjustedBlueColor(currentLightness);
  const darkColor = `hsl(210, 30%, ${Math.max(20, currentLightness - 20)}%)`;
  document.getElementById('colorPreview').style.background = 
    `linear-gradient(135deg, ${darkColor} 0%, ${color} 100%)`;
  
  console.log(`Lightness adjusted to: ${currentLightness}%`);
}

// Reset lightness to default
function resetLightness() {
  currentLightness = 55;
  document.getElementById('lightnessSlider').value = 55;
  updateLightness(55);
}

// Apply the adjusted lightness
function applyLightness() {
  // Save to localStorage
  localStorage.setItem('darkBlueLightness', currentLightness);
  
  // Apply the dark-blue theme with adjusted colors
  const adjustedBlue = getAdjustedBlueColor(currentLightness);
  const adjustedDark = `hsl(210, 30%, ${Math.max(20, currentLightness - 20)}%)`;
  const adjustedAccent = `hsl(204, 70%, ${Math.min(80, currentLightness + 10)}%)`;
  
  // Create custom theme
  const customTheme = {
    name: 'Dark Blue (Custom)',
    gradient: `linear-gradient(135deg, ${adjustedDark} 0%, ${adjustedBlue} 100%)`,
    primary: adjustedDark,
    secondary: adjustedBlue,
    accent: adjustedAccent
  };
  
  // Update body background gradient
  document.body.style.background = customTheme.gradient;
  
  // Update all gradient buttons
  const buttons = document.querySelectorAll('.card-btn');
  buttons.forEach(btn => {
    btn.style.background = customTheme.gradient;
  });
  
  // Update name color
  const nameElements = document.querySelectorAll('.gradient-name');
  nameElements.forEach(el => {
    el.style.color = adjustedBlue;
    el.style.textShadow = `2px 2px 4px ${adjustedBlue}4D`;
  });
  
  // Update progress bar
  const progressBar = document.getElementById('myBar');
  if (progressBar) {
    progressBar.style.background = customTheme.gradient;
  }
  
  // Update CSS variables
  document.documentElement.style.setProperty('--theme-primary', adjustedDark);
  document.documentElement.style.setProperty('--theme-secondary', adjustedBlue);
  document.documentElement.style.setProperty('--theme-accent', adjustedAccent);
  
  // Close adjuster
  closeColorAdjuster();
  
  console.log(`✅ Applied custom dark-blue theme with lightness: ${currentLightness}%`);
  console.log(`Primary: ${adjustedDark}`);
  console.log(`Secondary: ${adjustedBlue}`);
  console.log(`Accent: ${adjustedAccent}`);
}

// Click outside to close
document.addEventListener('click', function(event) {
  const adjuster = document.getElementById('colorAdjuster');
  const button = document.querySelector('.theme-switcher');
  const menu = document.getElementById('themeMenu');
  
  if (adjuster && !adjuster.contains(event.target) && 
      !button.contains(event.target) && 
      !menu.contains(event.target)) {
    adjuster.classList.remove('show');
  }
});
