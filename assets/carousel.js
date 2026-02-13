/**
 * Carousel: dot tracking + dot click navigation.
 */

/* --- Scroll event: update active dot --- */
document.addEventListener('scroll', function(e) {
    var track = e.target;
    if (!track.classList || !track.classList.contains('carousel-track')) return;

    var slides = track.querySelectorAll('.carousel-slide');
    var dots = track.parentElement.querySelectorAll('.carousel-dot');
    if (!slides.length || !dots.length) return;

    var scrollLeft = track.scrollLeft;
    var slideWidth = track.offsetWidth;
    var activeIndex = Math.round(scrollLeft / slideWidth);

    dots.forEach(function(dot, i) {
        if (i === activeIndex) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}, true);

/* --- Dot click: navigate to slide --- */
document.addEventListener('click', function(e) {
    if (!e.target.classList || !e.target.classList.contains('carousel-dot')) return;

    var dotsContainer = e.target.parentElement;
    var dots = dotsContainer.querySelectorAll('.carousel-dot');
    var track = dotsContainer.parentElement.querySelector('.carousel-track');
    if (!track) return;

    var index = Array.prototype.indexOf.call(dots, e.target);
    track.scrollTo({
        left: index * track.offsetWidth,
        behavior: 'smooth'
    });
});
