document.addEventListener('DOMContentLoaded', function() {
    const dossiersCtx = document.getElementById('dossiersChart').getContext('2d');
    new Chart(dossiersCtx, {
        type: 'bar',
        data: {
            labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'],
            datasets: [{
                label: 'Dossiers traités',
                data: [12, 19, 3, 5, 2, 8, 15, 10, 7, 11, 6, 14],
                backgroundColor: 'rgba(0, 123, 255, 0.7)',
                borderColor: 'rgba(0, 123, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                title: {
                    display: false
                }
            }
        }
    });

    // Data for Revenu Chart
    const revenuCtx = document.getElementById('revenuChart').getContext('2d');
    new Chart(revenuCtx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'],
            datasets: [{
                label: 'Revenus (€)',
                data: [2500, 3000, 1800, 3500, 2200, 4000, 3200, 2800, 3800, 4500, 3000, 5000],
                fill: true,
                backgroundColor: 'rgba(40, 167, 69, 0.2)',
                borderColor: 'rgba(40, 167, 69, 1)',
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                title: {
                    display: false
                }
            }
        }
    });
});