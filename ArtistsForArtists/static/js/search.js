let input = document.querySelector('input');
input.addEventListener('input', async function () {
    let response = await fetch('/search?q=' + input.value, {
        method: "POST",
    });
    let subdomains = await response.json();
    let html = '';
    for (let i in subdomains) {
        let subdomain = subdomains[i].replace('<', '&lt;').replace('&', '&amp;');
        html += '<li><a href=\"/r/' + subdomain + '\">' + subdomain + '</a></li>';
    }
    document.querySelector('#jsSearch').innerHTML = html;
});