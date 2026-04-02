let myLineChart = null;

function loadEmployeeHistory() {
    const matricule = document.getElementById('matriculeInput').value;
    const dateDebut = document.getElementById('dateDebut').value;
    const dateFin = document.getElementById('dateFin').value;

    const tableBody = document.getElementById('historyTableBody');
    const employeeNameElem = document.getElementById('employeeName');
    const chartCanvas = document.getElementById('employeeLineChart');

    // 1. Vérification et construction de l'URL
    let url = "";
    if (matricule && dateDebut && dateFin) {
        url = `/api/history/${matricule}?start=${dateDebut}&end=${dateFin}`;
    } else {
        alert("Veuillez remplir tous les champs (Matricule, Date de début, Date de fin).");
        return;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Données introuvables pour cette période');
            return response.json();
        })
        .then(data => {
            // 2. Mise à jour des en-têtes
            if (employeeNameElem) {
                employeeNameElem.innerText = `Historique de : ${data.nom_complet}`;
            }
            document.getElementById('displayMatricule').innerText = matricule;

            let html = '';
            let joursPresents = 0;
            let totalHeuresCumulees = 0;

            // 3. Boucle dynamique sur les données renvoyées par le serveur
            // C'est ici qu'on affiche TOUS les jours demandés sans exception
            data.raw_data.forEach(record => {
                const estPresent = record.heure_arrivee !== "--:--";
                
                if (estPresent) {
                    joursPresents++;
                    totalHeuresCumulees += parseFloat(record.duree_h);
                }

                // Définition des styles selon la présence
                const rowStyle = estPresent ? "" : "style='background-color: #fcfcfc;'";
                const badgeClass = estPresent ? "status-badge present" : "status-badge absent";
                const statutTexte = estPresent ? "Présent" : "Absent";

                html += `
                    <tr ${rowStyle}>
                        <td>
                            <div class="cell-icon">
                                <i class="fas fa-calendar-alt"></i> ${record.date_jour}
                            </div>
                        </td>
                        <td><span class="${badgeClass}">${statutTexte}</span></td>
                        <td class="${estPresent ? 'text-success font-weight-bold' : 'text-muted'}">
                            <div class="cell-icon">
                                <i class="fas fa-sign-in-alt"></i> ${record.heure_arrivee}
                            </div>
                        </td>
                        <td class="${estPresent ? 'text-danger font-weight-bold' : 'text-muted'}">
                            <div class="cell-icon">
                                <i class="fas fa-sign-out-alt"></i> ${record.heure_sortie}
                            </div>
                        </td>
                        <td>
                            <div class="cell-icon">
                                <i class="fas fa-stopwatch"></i> ${record.duree_h} h
                            </div>
                        </td>
                    </tr>`;
            });

            // Injection du HTML
            tableBody.innerHTML = html;

            // 4. Mise à jour des cartes de statistiques
            document.getElementById('totalPresents').innerText = joursPresents;
            document.getElementById('totalAbsents').innerText = data.raw_data.length - joursPresents;
            document.getElementById('totalHours').innerText = totalHeuresCumulees.toFixed(2) + "h";

            // 5. Génération du graphique
            if (chartCanvas) {
                const ctx = chartCanvas.getContext('2d');
                if (myLineChart) myLineChart.destroy();

                myLineChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.dates || [],
                        datasets: [
                            {
                                label: 'Arrivée',
                                data: data.heures_arrivee || [],
                                borderColor: '#4e73df',
                                backgroundColor: 'rgba(78, 115, 223, 0.1)',
                                tension: 0.3,
                                fill: false,
                                spanGaps: true // Permet de relier les points même s'il y a des jours absents
                            },
                            {
                                label: 'Sortie',
                                data: data.heures_sortie || [],
                                borderColor: '#e74a3b',
                                backgroundColor: 'rgba(231, 74, 59, 0.1)',
                                tension: 0.3,
                                fill: false,
                                spanGaps: true
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false
                        },
                        scales: {
                            y: {
                                suggestedMin: 7,
                                suggestedMax: 19,
                                ticks: {
                                    callback: function (value) { return value + "h"; }
                                }
                            }
                        },
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    afterBody: function (context) {
                                        const index = context[0].dataIndex;
                                        const duree = data.durees?.[index] || 0;
                                        return `\nTotal travaillé : ${duree} heures`;
                                    },
                                    label: function (context) {
                                        let label = context.dataset.label || '';
                                        const val = context.parsed.y;
                                        if (val === null) return label + ": Absent";
                                        
                                        const h = Math.floor(val);
                                        const m = Math.round((val - h) * 60);
                                        return label + ": " + h + "h" + (m < 10 ? '0' : '') + m;
                                    }
                                }
                            }
                        }
                    }
                });
            }
        })
        .catch(error => {
            console.error(error);
            alert("Erreur : " + error.message);
        });
}