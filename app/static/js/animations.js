// app/static/js/animations.js

document.addEventListener('DOMContentLoaded', () => {

    // Initialize GSAP
    gsap.registerPlugin(ScrollTrigger);

    // --- Component-Level Motion: Staggered Card Animation ---
    const cards = gsap.utils.toArray('.card');
    cards.forEach(card => {
        gsap.from(card, {
            opacity: 0,
            y: 50,
            duration: 0.5,
            scrollTrigger: {
                trigger: card,
                start: 'top 80%',
                toggleActions: 'play none none none',
            }
        });
    });

    // --- Kinetic Typography: Animate Headings ---
    const headings = gsap.utils.toArray('h1, h2, h3');
    headings.forEach(heading => {
        gsap.from(heading, {
            opacity: 0,
            y: 20,
            duration: 0.5,
            delay: 0.2,
            scrollTrigger: {
                trigger: heading,
                start: 'top 90%',
                toggleActions: 'play none none none',
            }
        });
    });

    // --- Micro-interactions: Button Animations ---
    const buttons = gsap.utils.toArray('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', () => {
            gsap.to(button, { scale: 1.05, duration: 0.2 });
        });
        button.addEventListener('mouseleave', () => {
            gsap.to(button, { scale: 1, duration: 0.2 });
        });
        button.addEventListener('mousedown', () => {
            gsap.to(button, { scale: 0.95, duration: 0.1 });
        });
        button.addEventListener('mouseup', () => {
            gsap.to(button, { scale: 1, duration: 0.1 });
        });
    });

});
