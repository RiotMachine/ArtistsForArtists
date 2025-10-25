// Implements Dark Mode
document.addEventListener('DOMContentLoaded', function () {
    document.querySelector('#darkmode').addEventListener('click', function () {
		fetch('/darkmode', {
			method: "POST",
		})
		.then(response => response.json())
		.then(data => {
			if (data.darkmode_val) {
				document.documentElement.setAttribute('data-bs-theme', 'dark');
			}
			else {
				document.documentElement.setAttribute('data-bs-theme', 'light');
			}
		})
		.catch(error => console.error('Error:', error));
    });
});