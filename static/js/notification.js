document.addEventListener('DOMContentLoaded', async () => {
    // =========================================================================
    // SECTION 1 : GESTION DE LA CONFIGURATION (FORMULAIRE)
    // =========================================================================
    const notifForm = document.getElementById('notification-form');
    const msgBox = document.getElementById('notif-message');
    
    const inputDateDebut = document.getElementById('date_debut');
    const inputDateFin = document.getElementById('date_fin');
    
    if (notifForm) {
        const loadUrl = `${notifForm.getAttribute('data-load-url')}?_=${Date.now()}`;
        const saveUrl = notifForm.getAttribute('data-url');

        try {
            const res = await fetch(loadUrl);
            const resData = await res.json();
            
            if (resData.status === 'success' && resData.data) {
                inputDateDebut.value = resData.data.date_debut;
                inputDateFin.value = resData.data.date_fin;
                document.getElementById('day_of_week').value = resData.data.cron_day_of_week;
                document.getElementById('send_time').value = `${resData.data.cron_hour.padStart(2, '0')}:${resData.data.cron_minute.padStart(2, '0')}`;
            }
        } catch (err) {
            console.error("Impossible de charger la config initiale", err);
        }

        notifForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const [hour, minute] = document.getElementById('send_time').value.split(':');
            const payload = {
                date_debut: inputDateDebut.value,
                date_fin: inputDateFin.value,
                day_of_week: document.getElementById('day_of_week').value,
                hour: parseInt(hour, 10).toString(),
                minute: parseInt(minute, 10).toString()
            };

            const btn = notifForm.querySelector('button[type="submit"]');
            const btnText = btn.querySelector('.btn-text');
            const btnSpinner = btn.querySelector('.spinner');

            try {
                btn.disabled = true;
                btnText.textContent = 'Déploiement...';
                btnSpinner.style.display = 'inline-block';

                const response = await fetch(saveUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();
                msgBox.style.display = 'block';
                
                if (response.ok) {
                    msgBox.className = 'feedback-msg badge success';
                    msgBox.innerHTML = `<i class="fas fa-check-circle"></i> ${result.message}`;
                } else {
                    msgBox.className = 'feedback-msg badge error';
                    msgBox.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${result.message}`;
                }
            } catch (error) {
                msgBox.className = 'feedback-msg badge error';
                msgBox.innerHTML = `<i class="fas fa-times-circle"></i> Connexion réseau interrompue avec le serveur.`;
            } finally {
                btn.disabled = false;
                btnText.textContent = 'Enregistrer et Déployer la règle';
                btnSpinner.style.display = 'none';
            }
        });
    }

    // =========================================================================
    // SECTION 2 : HISTORIQUE ET SCROLL VIRTUEL (AVEC AUTO-REFRESH)
    // =========================================================================
    const ROW_HEIGHT = 45;      
    const VISIBLE_ROWS = 10;    
    const BUFFER_ROWS = 2;      
    const REFRESH_INTERVAL = 10000; // Rafraîchissement automatique toutes les 10 secondes (10000 ms)

    let rawNotifications = [];  
    let filteredNotifications = []; 
    let refreshTimer = null; // Variable pour stocker la boucle temporelle
    
    const scrollContainer = document.getElementById('scroll-container');
    const tableSpacer = document.getElementById('table-spacer');
    const tableContent = document.getElementById('table-content');
    const searchInput = document.getElementById('search-matricules');
    const searchCount = document.getElementById('search-count');
    const selectAllVisible = document.getElementById('select-all-visible');
    const selectionStatus = document.getElementById('selection-status');
    const btnResend = document.getElementById('btn-resend');

    if (scrollContainer && tableContent) {

        // 2.1 Récupération optimisée : met à jour l'historique sans perdre la sélection de l'utilisateur
        async function fetchHistory() {
            try {
                const response = await fetch(`/api/admin/notifications/history?_=${Date.now()}`);
                const result = await response.json();
                
                if (result.status === 'success') {
                    // ÉTAPE CRUCIALE : On sauvegarde temporairement les IDs des lignes actuellement sélectionnées
                    const selectedIds = new Set(
                        rawNotifications.filter(item => item.selected).map(item => item.id)
                    );

                    // On reconstruit le tableau brut en ré-appliquant l'état sélectionné
                    rawNotifications = result.data.map(item => ({ 
                        ...item, 
                        selected: selectedIds.has(item.id) 
                    }));

                    applyFilterAndRender();
                }
            } catch (error) {
                console.error("Erreur de chargement de l'historique:", error);
            }
        }

        // 2.2 Gestion de la boucle de rafraîchissement automatique
        function startAutoRefresh() {
            if (!refreshTimer) {
                refreshTimer = setInterval(fetchHistory, REFRESH_INTERVAL);
            }
        }

        function stopAutoRefresh() {
            if (refreshTimer) {
                clearInterval(refreshTimer);
                refreshTimer = null;
            }
        }

        // 2.3 Filtrage
        function applyFilterAndRender() {
            const query = searchInput.value.trim().toLowerCase();
            
            if (!query) {
                filteredNotifications = [...rawNotifications];
            } else {
                const matriculesToSearch = query.split(';')
                                                .map(m => m.trim())
                                                .filter(m => m.length > 0);
                
                filteredNotifications = rawNotifications.filter(item => {
                    const itemMatricule = item.matricule.toLowerCase();
                    return matriculesToSearch.some(searchMat => itemMatricule.includes(searchMat));
                });
            }

            searchCount.textContent = `${filteredNotifications.length} ligne(s)`;
            tableSpacer.style.height = `${filteredNotifications.length * ROW_HEIGHT}px`;
            
            updateSelectAllState();
            renderVirtualRows();
        }

        // 2.4 Rendu visuel
        function renderVirtualRows() {
            const scrollTop = scrollContainer.scrollTop;
            
            let startIndex = Math.floor(scrollTop / ROW_HEIGHT) - BUFFER_ROWS;
            startIndex = Math.max(0, startIndex);
            
            let endIndex = startIndex + VISIBLE_ROWS + (BUFFER_ROWS * 2);
            endIndex = Math.min(filteredNotifications.length - 1, endIndex);

            const offsetY = startIndex * ROW_HEIGHT;
            tableContent.style.transform = `translateY(${offsetY}px)`;

            let html = '';
            for (let i = startIndex; i <= endIndex; i++) {
                const item = filteredNotifications[i];
                const dateObj = new Date(item.date_envoi);
                const formattedDate = `${dateObj.toLocaleDateString()} ${dateObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
                const badgeClass = item.statut === 'Succès' ? 'badge success' : 'badge error';
                
                const topPosition = (i - startIndex) * ROW_HEIGHT;

                html += `
                    <div class="v-table-row" style="top: ${topPosition}px;">
                        <div class="v-col col-check">
                            <input type="checkbox" class="row-checkbox" data-id="${item.id}" ${item.selected ? 'checked' : ''}>
                        </div>
                        <div class="v-col col-date">${formattedDate}</div>
                        <div class="v-col col-matricule">${item.matricule}</div>
                        <div class="v-col col-employe">
                            <strong>${item.nom} ${item.prenom}</strong><br>
                            <small style="color:#64748b;">${item.email}</small>
                        </div>
                        <div class="v-col col-statut">
                            <span class="${badgeClass}">${item.statut}</span>
                        </div>
                        <div class="v-col col-details" title="${item.message_erreur || ''}">
                            ${item.message_erreur || '-'}
                        </div>
                    </div>
                `;
            }

            tableContent.innerHTML = html;
            updateUISelectionStates();
        }

        // 2.5 Événements des cases à cocher
        tableContent.addEventListener('change', (e) => {
            if (e.target.classList.contains('row-checkbox')) {
                const id = parseInt(e.target.getAttribute('data-id'));
                const isChecked = e.target.checked;
                
                const itemRaw = rawNotifications.find(x => x.id === id);
                if (itemRaw) itemRaw.selected = isChecked;

                const itemFiltered = filteredNotifications.find(x => x.id === id);
                if (itemFiltered) itemFiltered.selected = isChecked;

                updateUISelectionStates();
                updateSelectAllState();
            }
        });

        selectAllVisible.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            filteredNotifications.forEach(item => {
                item.selected = isChecked;
                const rawItem = rawNotifications.find(x => x.id === item.id);
                if (rawItem) rawItem.selected = isChecked;
            });
            renderVirtualRows();
        });

        function updateSelectAllState() {
            if (filteredNotifications.length === 0) {
                selectAllVisible.checked = false;
                return;
            }
            const allChecked = filteredNotifications.every(item => item.selected);
            selectAllVisible.checked = allChecked;
        }

        function updateUISelectionStates() {
            const totalSelected = rawNotifications.filter(item => item.selected).length;
            selectionStatus.textContent = `${totalSelected} employé(s) sélectionné(s)`;
            btnResend.disabled = totalSelected === 0;
        }

        scrollContainer.addEventListener('scroll', renderVirtualRows);
        searchInput.addEventListener('input', applyFilterAndRender);

        // 2.6 Action : Envoi Groupé Ciblé
        btnResend.addEventListener('click', async () => {
            const selectedItems = rawNotifications.filter(item => item.selected);
            const employeIds = [...new Set(selectedItems.map(item => item.employe_id).filter(id => id))];

            if (employeIds.length === 0) {
                alert("Erreur : Aucun identifiant d'employé valide trouvé.");
                return;
            }

            const btnText = btnResend.querySelector('.btn-text');
            const btnSpinner = btnResend.querySelector('.spinner');

            btnResend.disabled = true;
            btnText.textContent = "Envoi en cours...";
            btnSpinner.style.display = "inline-block";

            try {
                // On met l'auto-refresh en pause pendant l'action d'envoi pour éviter des conflits réseau
                stopAutoRefresh();

                const response = await fetch('/api/admin/notifications/send_manual', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        employe_ids: employeIds,
                        date_debut: inputDateDebut.value, 
                        date_fin: inputDateFin.value
                    })
                });

                const result = await response.json();
                if (response.ok) {
                    alert(`Succès : ${result.message}`);
                    rawNotifications.forEach(x => x.selected = false);
                    await fetchHistory(); 
                } else {
                    alert(`Erreur du serveur : ${result.message}`);
                }
            } catch (error) {
                alert("Erreur réseau lors de la tentative de renvoi.");
            } finally {
                btnResend.disabled = false;
                btnText.textContent = "Renvoyer aux sélectionnés";
                btnSpinner.style.display = "none";
                // On relance la boucle automatique après l'envoi
                startAutoRefresh();
            }
        });

        // 2.7 Initialisation au chargement de la page
        fetchHistory();
        startAutoRefresh();

        // 2.8 Optimisation éco-système : arrêter les requêtes si l'utilisateur quitte l'onglet du tableau de bord
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                stopAutoRefresh();
            } else {
                fetchHistory(); // Une mise à jour immédiate au retour sur la page
                startAutoRefresh();
            }
        });
    }
});