document.addEventListener('DOMContentLoaded', function() {
    const api_url = '/api/stats/presence_7days';

    fetch(api_url)
        .then(response => {
            if (!response.ok) throw new Error('Erreur 404 ou Serveur');
            return response.json();
        })
        .then(data => {
            if (!data || data.length === 0) return;

            // Calcul des statistiques sur 7 jours
            const totalEnregistrements = data.length;
            const presentsTotal = data.filter(emp => emp.present === 1).length;
            const retardsTotal = data.filter(emp => emp.present === 1 && emp.arrivee > "08:30").length;
            const absentsTotal = data.filter(emp => emp.present === 0).length;

            // Créer le Pie Chart
            const ctx = document.getElementById('presence7DaysChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Présents à l\'heure', 'Retardataires', 'Absents'],
                    datasets: [{
                        data: [
                            presentsTotal - retardsTotal,
                            retardsTotal,
                            absentsTotal
                        ],
                        backgroundColor: [
                            'rgba(28, 200, 138, 0.8)',      // Vert pour présents ponctuel
                            'rgba(246, 194, 62, 0.8)',      // Orange pour retards
                            'rgba(231, 74, 59, 0.8)'        // Rouge pour absents
                        ],
                        borderColor: [
                            '#1cc88a',
                            '#f6c23e',
                            '#e74a3b'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                font: {
                                    size: 12,
                                    weight: '600'
                                },
                                padding: 15,
                                usePointStyle: true
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((context.parsed / total) * 100).toFixed(1);
                                    return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Erreur:', error);
        });
});
