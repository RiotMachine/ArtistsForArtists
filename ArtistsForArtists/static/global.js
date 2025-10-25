// Implements Dark Mode
document.addEventListener('DOMContentLoaded', function () {
	let darkmode_pref = document.getElementById('darkmode-pref');
	if (darkmode_pref) {
		let darkmode_val = JSON.parse(darkmode_pref.textContent)
		if (darkmode_val) {
			document.querySelector('body').style.backgroundColor = 'black';
			document.querySelector('body').style.color = 'white';
		}
		else {
			document.querySelector('body').style.backgroundColor = 'white';
			document.querySelector('body').style.color = 'black';
		}
	}
    document.querySelector('#darkmode').addEventListener('click', function () {
		fetch('/darkmode', {
			method: "POST",
		})
            .then(response => response.json())
            .then(data => {
				if (data.darkmode_val) {
					document.querySelector('body').style.backgroundColor = 'black';
					document.querySelector('body').style.color = 'white';
				}
				else {
					document.querySelector('body').style.backgroundColor = 'white';
					document.querySelector('body').style.color = 'black';
				}
            })
            .catch(error => console.error('Error:', error));
    });
});