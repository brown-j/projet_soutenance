// static/js/photos.js

function previewPhoto(input, previewId) {
    const previewContainer = document.getElementById(previewId);
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            // Chercher l'image existante ou le placeholder
            let img = previewContainer.querySelector('img');
            
            if (!img) {
                // Si l'image n'existe pas (cas de l'ajout), on la crée
                img = document.createElement('img');
                img.classList.add('photo-img', 'full');
                previewContainer.innerHTML = ''; // On vide le placeholder (l'icône)
                previewContainer.appendChild(img);
            }
            
            img.src = e.target.result; // On met à jour la source avec l'image choisie
        };

        reader.readAsDataURL(input.files[0]);
    }
}

function clearPhoto(previewId, inputName) {
    const previewContainer = document.getElementById(previewId);
    const input = document.querySelector(`input[name="${inputName}"]`);
    
    // Réinitialiser l'input file
    if(input) input.value = '';
    
    // Remettre le placeholder par défaut
    previewContainer.innerHTML = `
        <div class="photo-placeholder">
            <i class="fa-solid fa-user"></i>
        </div>
    `;
}

/**
 * Génère le HTML d'un input photo avec preview dynamique
 * @param {string} slotId - Identifiant unique (ex: 'main')
 * @param {string} initialPhotoUrl - URL de la photo existante (null si ajout)
 * @param {string} inputName - Nom de l'input pour le backend (ex: 'photo')
 * @returns {string} HTML string
 */
function generatePhotoInputHTML(slotId, initialPhotoUrl, inputName) {
    // Vérification si une photo existe pour choisir le contenu de la preview
    const hasPhoto = initialPhotoUrl && initialPhotoUrl !== 'None' && initialPhotoUrl !== '';
    
    const previewContent = hasPhoto 
        ? `<img src="${initialPhotoUrl}" class="photo-img full">`
        : `<div class="photo-placeholder"><i class="fa-solid fa-user"></i></div>`;
        
    return `
        <div class="photo-slot">
            <div class="photo-preview" id="preview-${slotId}">
                ${previewContent}
            </div>

            <input type="file" 
                   name="${inputName}" 
                   accept="image/*" 
                   onchange="previewPhoto(this, 'preview-${slotId}')">

            <button type="button" 
                    class="delete-photo" 
                    onclick="clearPhoto('preview-${slotId}', '${inputName}')">
                🗑 Supprimer
            </button>
        </div>
    `;
}