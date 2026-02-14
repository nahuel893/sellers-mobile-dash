/**
 * Carousel: dot tracking, dot click navigation, global category toggle.
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

/* --- Category toggle: scroll ALL carousels to the same slide --- */
document.addEventListener('click', function(e) {
    if (!e.target.classList || !e.target.classList.contains('category-btn')) return;

    var slideIndex = parseInt(e.target.getAttribute('data-slide'), 10);

    // Update active button state on ALL toggles
    document.querySelectorAll('.category-toggle').forEach(function(toggle) {
        toggle.querySelectorAll('.category-btn').forEach(function(btn) {
            if (parseInt(btn.getAttribute('data-slide'), 10) === slideIndex) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    });

    // Scroll ALL carousel tracks to target slide
    document.querySelectorAll('.carousel-track').forEach(function(track) {
        track.scrollTo({
            left: slideIndex * track.offsetWidth,
            behavior: 'smooth'
        });
    });
});
