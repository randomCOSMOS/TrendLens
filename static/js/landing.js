document.addEventListener('DOMContentLoaded', function() {
    const followers = document.querySelectorAll('.preview-followers');
    followers.forEach(follower => {
        const text = follower.textContent;
        follower.style.opacity = '0';
        setTimeout(() => {
            follower.style.opacity = '1';
            follower.style.transition = 'all 0.5s ease';
        }, Math.random() * 1000 + 1000);
    });

    document.addEventListener('mousemove', (e) => {
        const preview = document.querySelector('.dashboard-preview');
        const x = (e.clientX / window.innerWidth) * 100;
        const y = (e.clientY / window.innerHeight) * 100;
        
        preview.style.transform = `translateY(-5px) scale(1.02) rotateY(${(x - 50) * 0.1}deg) rotateX(${(y - 50) * -0.1}deg)`;
    });

    document.addEventListener('mouseleave', () => {
        const preview = document.querySelector('.dashboard-preview');
        preview.style.transform = 'translateY(-5px) scale(1.02)';
    });
});