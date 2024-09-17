function showCities(problem) {
    document.getElementById('problems').style.display = 'none';
    document.getElementById('cities').style.display = 'block';
    document.getElementById('selected-problem').innerText = `Cities Affected by ${capitalize(problem)}`;

    const cityTiles = document.querySelectorAll('.city-tile');
    cityTiles.forEach(tile => {
        tile.onclick = () => showReport(tile.getAttribute('data-city'));
    });
}

function showReport(city) {
    document.getElementById('cities').style.display = 'none';
    document.getElementById('report').style.display = 'block';
    document.getElementById('selected-city').innerText = capitalize(city);

    fetch(`/report/flood/${city}`)
        .then(response => response.json())
        .then(data => {
            let reportContent = '';
            if (data.report && data.report.length > 0) {
                data.report.forEach(item => {
                    reportContent += `<h3>${item.title}</h3>
                                      <p>${item.description}</p>
                                      <p><strong>Date:</strong> ${item.date}</p>
                                      <p><strong>Location:</strong> ${item.location}</p>
                                      <p><strong>Rainfall:</strong> ${item.rainfall}</p>
                                      <p><strong>Casualties:</strong> ${item.casualties}</p>
                                      <hr>`;
                });
            } else {
                reportContent = 'No updates available yet.';
            }
            document.getElementById('report-content').innerHTML = reportContent;
        })
        .catch(error => {
            document.getElementById('report-content').innerText = 'Error fetching report';
        });
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
