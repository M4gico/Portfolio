// Mobile Menu Toggle
function toggleMenu() {
  const mobileMenu = document.querySelector('.mobile-menu');
  const menuIcon = document.querySelector('.menu-icon');
  
  mobileMenu.classList.toggle('active');
  menuIcon.classList.toggle('active');
}

// Close mobile menu when clicking on a link
document.addEventListener('DOMContentLoaded', function() {
  const mobileMenuLinks = document.querySelectorAll('.mobile-menu a');
  
  mobileMenuLinks.forEach(link => {
    link.addEventListener('click', () => {
      const mobileMenu = document.querySelector('.mobile-menu');
      const menuIcon = document.querySelector('.menu-icon');
      
      mobileMenu.classList.remove('active');
      menuIcon.classList.remove('active');
    });
  });
});

// Smooth Scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    
    if (target) {
      const offsetTop = target.offsetTop - 80; // Adjust for fixed nav
      window.scrollTo({
        top: offsetTop,
        behavior: 'smooth'
      });
    }
  });
});

// Project Carousel Navigation
function setupCarousel(containerId, prevBtnId, nextBtnId) {
  const container = document.getElementById(containerId);
  const prevBtn = document.getElementById(prevBtnId);
  const nextBtn = document.getElementById(nextBtnId);
  
  if (!container || !prevBtn || !nextBtn) return;
  
  prevBtn.addEventListener('click', () => {
    container.scrollBy({
      left: -350,
      behavior: 'smooth'
    });
  });
  
  nextBtn.addEventListener('click', () => {
    container.scrollBy({
      left: 350,
      behavior: 'smooth'
    });
  });
}

// Initialize all carousels
document.addEventListener('DOMContentLoaded', function() {
  setupCarousel('academic-container', 'academic-pre-btn', 'academic-nxt-btn');
  setupCarousel('personal-container', 'personal-pre-btn', 'personal-nxt-btn');
  setupCarousel('internship-container', 'internship-pre-btn', 'internship-nxt-btn');
});

// Navbar background change on scroll
window.addEventListener('scroll', function() {
  const nav = document.getElementById('nav');
  
  if (window.scrollY > 100) {
    nav.style.background = 'rgba(0, 0, 0, 0.95)';
    nav.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.5)';
  } else {
    nav.style.background = 'rgba(0, 0, 0, 0.9)';
    nav.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.3)';
  }
});

// Animate elements on scroll
const observerOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, observerOptions);

// Observe all project cards
document.addEventListener('DOMContentLoaded', function() {
  const cards = document.querySelectorAll('.experience-card');
  
  cards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(30px)';
    card.style.transition = 'all 0.6s ease';
    observer.observe(card);
  });
});
