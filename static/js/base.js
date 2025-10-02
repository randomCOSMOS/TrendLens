setTimeout(() => {
            document.querySelectorAll('.flash-message').forEach(msg => {
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-1rem)';
                setTimeout(() => msg.remove(), 300);
            });
        }, 5000);