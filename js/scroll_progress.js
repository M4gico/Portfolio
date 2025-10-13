// Scroll Progress Bar
window.onscroll = function() {
  updateProgressBar();
};

function updateProgressBar() {
  const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
  const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
  const scrolled = (winScroll / height) * 100;
  
  const progressBar = document.getElementById("myBar");
  if (progressBar) {
    progressBar.style.width = scrolled + "%";
  }
}
