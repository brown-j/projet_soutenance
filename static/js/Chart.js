document.addEventListener('DOMContentLoaded', function() {
    const api_url = '/api/stats/presence_today';

    fetch(api_url)
        .then(response => {
            if (!response.ok) throw new Error('Erreur 404 ou Serveur');
            return response.json();
        })
        .then(data => {
            if (data.length === 0) return;

            // Préparation du Graphique
            const labels = data.map(emp => `${emp.prenom} ${emp.nom}`);
            const durees = data.map(emp => emp.duree);

            const ctx = document.getElementById('presenceChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Heures travaillées',
                        data: durees,
                        backgroundColor: 'rgba(78, 115, 223, 0.8)',
                        hoverBackgroundColor: '#2e59d9',
                        borderColor: '#4e73df',
                        borderWidth: 1
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, max: 12 }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Erreur:', error);
            // Optionnel: Afficher un message si l'API ne répond pas
        });
});

// Diagramme Circulaire (Doughnut) pour les 7 derniers jours
const ctxWeekly = document.getElementById('weeklyStatusChart').getContext('2d');
const weeklyChart = new Chart(ctxWeekly, {
    type: 'doughnut',
    data: {
        labels: ['Présents', 'Absents', 'En Retard'],
        datasets: [{
            data: [65, 20, 15], // Données exemples, à remplacer par ton fetch API
            backgroundColor: ['#2ecc71', '#e74c3c', '#f1c40f'],
            borderWidth: 0
        }]
    },
    options: {
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
            legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } }
        }
    }
});