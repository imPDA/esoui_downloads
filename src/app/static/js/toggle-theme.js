document.addEventListener('DOMContentLoaded', (event) => {
    const themeToggle = document.getElementById('theme-toggle');
    const themeText = document.querySelector('.theme-text');

    themeToggle.addEventListener('change', function() {
        if (this.checked) {
            document.body.classList.add('light-theme');
            themeText.textContent = 'Light Mode';
        } else {
            document.body.classList.remove('light-theme');
            themeText.textContent = 'Dark Mode';
        }
    });
});