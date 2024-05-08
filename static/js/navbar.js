
//  Below causes NavBar to disappear when scrolling down and appear when scrolling up

let lastScrollTop = 0;
window.addEventListener("scroll", function(){
   var currentScroll = window.pageYOffset || document.documentElement.scrollTop;
   if (currentScroll > lastScrollTop){
      // scroll down
      document.querySelector('.navbar').style.top='-60px'; // adjust '-60px' to the height of your navbar
   } else {
      // scroll up
      document.querySelector('.navbar').style.top='0px';
   }
   lastScrollTop = currentScroll <= 0 ? 0 : currentScroll; // For Mobile or negative scrolling
}, false);