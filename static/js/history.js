let myLineChart = null;

// --- VARIABLES GLOBALES POUR L'EXPORT ---
let currentHistoryData = null;
let currentMatricule = "";

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
            // SAUVEGARDE DES DONNÉES POUR LES EXPORTS
            currentHistoryData = data;
            currentMatricule = matricule;

            // 2. Mise à jour des en-têtes
            if (employeeNameElem) {
                employeeNameElem.innerText = `Historique de : ${data.nom_complet}`;
            }
            document.getElementById('displayMatricule').innerText = matricule;

            let html = '';
            let joursPresents = 0;
            let totalHeuresCumulees = 0;

            // 3. Boucle dynamique sur les données renvoyées par le serveur
            data.raw_data.forEach(record => {
                const estPresent = record.heure_arrivee !== "--:--";

                if (estPresent) {
                    joursPresents++;
                    totalHeuresCumulees += parseFloat(record.duree_h);
                }

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
                                spanGaps: true
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

// --- EXPORTATION CSV (Déclenché par le bouton CSV) ---
function exportHistoryToCSV() {
    if (!currentHistoryData || !currentHistoryData.raw_data) {
        alert("Aucune donnée disponible pour l'exportation. Veuillez d'abord charger un historique.");
        return;
    }

    let csvContent = "\uFEFF";
    csvContent += "Matricule;Nom Complet;Date;Statut;Heure Arrivée;Heure Sortie;Durée (h)\r\n";

    currentHistoryData.raw_data.forEach(record => {
        const estPresent = record.heure_arrivee !== "--:--";
        const statutTexte = estPresent ? "Présent" : "Absent";

        const line = [
            currentMatricule,
            currentHistoryData.nom_complet,
            record.date_jour,
            statutTexte,
            record.heure_arrivee,
            record.heure_sortie,
            record.duree_h
        ].join(";");

        csvContent += line + "\r\n";
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    const dateFichier = new Date().toISOString().slice(0, 10);
    link.setAttribute("download", `export_${currentMatricule}_${dateFichier}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// --- EXPORTATION PDF VECTORIEL (Déclenché par le bouton Imprimer) ---
function printHistory() {
    if (!currentHistoryData || !currentHistoryData.raw_data) {
        alert("Aucune donnée disponible pour l'impression PDF. Veuillez d'abord charger un historique.");
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF(); 

    // --- Design de l'en-tête du document ---
    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);
    doc.setTextColor(15, 23, 42); 
    doc.text("PresenceApp", 14, 20);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(12);
    doc.setTextColor(100, 116, 139); 
    doc.text("Rapport Officiel des Présences", 14, 28);

    doc.setDrawColor(226, 232, 240);
    doc.line(14, 32, 196, 32);

    // --- Section Informations ---
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(15, 23, 42);
    doc.text("Informations Employé", 14, 42);

    doc.setFont("helvetica", "normal");
    doc.text(`Nom complet : ${currentHistoryData.nom_complet}`, 14, 48);
    doc.text(`Matricule : ${currentMatricule}`, 14, 54);
    
    // Recalcul des métriques rapides pour le PDF
    let joursPresents = 0;
    let totalHeures = 0;
    currentHistoryData.raw_data.forEach(r => {
        if (r.heure_arrivee !== "--:--") {
            joursPresents++;
            totalHeures += parseFloat(r.duree_h);
        }
    });
    const joursAbsents = currentHistoryData.raw_data.length - joursPresents;

    // --- Section Résumé ---
    doc.setFont("helvetica", "bold");
    doc.text("Résumé de la période", 120, 42);
    doc.setFont("helvetica", "normal");
    doc.text(`Jours présents : ${joursPresents}`, 120, 48);
    doc.text(`Jours absents : ${joursAbsents}`, 120, 54);
    doc.text(`Total heures : ${totalHeures.toFixed(2)}h`, 120, 60);

    // Variable pour suivre la position verticale sur le document PDF
    let finalY = 70; 

    // --- 📸 CAPTURE ET INSERTION DU GRAPHIQUE ---
    const canvas = document.getElementById('employeeLineChart');
    if (canvas) {
        // 1. On extrait l'image du canvas au format PNG
        const canvasImg = canvas.toDataURL('image/png', 1.0);
        
        // 2. On calcule les dimensions pour qu'il prenne toute la largeur (182mm)
        const pdfWidth = 182; 
        const pdfHeight = (canvas.height * pdfWidth) / canvas.width; // Maintient les proportions
        
        // 3. On ajoute un fond blanc pour éviter un fond noir dû à la transparence du canvas
        doc.setFillColor(255, 255, 255);
        doc.rect(14, finalY, pdfWidth, pdfHeight, 'F');
        
        // 4. On colle l'image dans le document
        doc.addImage(canvasImg, 'PNG', 14, finalY, pdfWidth, pdfHeight);
        
        // 5. On décale la position finale (finalY) vers le bas pour ne pas que le tableau chevauche le graphique
        finalY += pdfHeight + 10; 
    }

    // --- Génération propre du tableau (AutoTable) ---
    const colonnes = ["Date", "Statut", "Heure Arrivée", "Heure Départ", "Durée (h)"];
    const lignes = [];

    currentHistoryData.raw_data.forEach(record => {
        const estPresent = record.heure_arrivee !== "--:--";
        const statut = estPresent ? "Présent" : "Absent";
        
        lignes.push([
            record.date_jour,
            statut,
            record.heure_arrivee,
            record.heure_sortie,
            record.duree_h
        ]);
    });

    doc.autoTable({
        startY: finalY, // Le tableau commencera dynamiquement SOUS le graphique
        head: [colonnes],
        body: lignes,
        theme: 'striped', 
        headStyles: { 
            fillColor: [78, 115, 223], 
            textColor: 255,
            fontStyle: 'bold'
        },
        alternateRowStyles: {
            fillColor: [248, 250, 252] 
        },
        didParseCell: function(data) {
            if (data.section === 'body' && data.column.index === 1) {
                if (data.cell.raw === 'Absent') {
                    data.cell.styles.textColor = [231, 74, 59]; 
                    data.cell.styles.fontStyle = 'bold';
                } else {
                    data.cell.styles.textColor = [28, 200, 138]; 
                    data.cell.styles.fontStyle = 'bold';
                }
            }
        }
    });

    // --- Calcul et écriture automatique des numéros de pages ---
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(9);
        doc.setTextColor(150);
        doc.text(`Page ${i} sur ${pageCount}`, 196, 285, { align: 'right' });
        const dateGen = new Date().toLocaleDateString('fr-FR');
        doc.text(`Document généré le ${dateGen}`, 14, 285);
    }

    // Sauvegarde automatique du fichier
    const dateFichier = new Date().toISOString().slice(0, 10);
    doc.save(`Rapport_Presence_${currentMatricule}_${dateFichier}.pdf`);
}