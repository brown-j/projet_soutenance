function previewPhoto(input, slotId) {
    const previewContainer = document.getElementById(`preview-${slotId}`);
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            // On cherche l'élément qui contient l'image ou l'icône
            let displayZone = previewContainer.querySelector('.photo-display-zone');
            
            // On remplace le contenu par la nouvelle image
            displayZone.innerHTML = `<img src="${e.target.result}" class="photo-img full">`;
            
            // On affiche le bouton supprimer (au cas où il était caché)
            const deleteBtn = previewContainer.querySelector('.btn-delete');
            if(deleteBtn) deleteBtn.style.display = 'flex';
        };

        reader.readAsDataURL(input.files[0]);
    }
}

function clearPhoto(slotId) {
    const previewContainer = document.getElementById(`preview-${slotId}`);
    const input = document.getElementById(`input-${slotId}`);
    
    // 1. Réinitialiser l'input file
    if(input) input.value = '';
    
    // 2. Remettre le placeholder (icône utilisateur)
    const displayZone = previewContainer.querySelector('.photo-display-zone');
    displayZone.innerHTML = `<div class="photo-placeholder"><i class="fa-solid fa-user"></i></div>`;
    
    // 3. Optionnel : Cacher le bouton supprimer si vide
    const deleteBtn = previewContainer.querySelector('.btn-delete');
    if(deleteBtn) deleteBtn.style.display = 'none';
}

/**
 * Génère le HTML d'un input photo
 */
function generatePhotoInputHTML(slotId, initialPhotoUrl, inputName) {
    const hasPhoto = initialPhotoUrl && initialPhotoUrl !== 'None' && initialPhotoUrl !== '';
    
    const imageHtml = hasPhoto 
        ? `<img src="${initialPhotoUrl}" class="photo-img full">`
        : `<div class="photo-placeholder"><i class="fa-solid fa-user"></i></div>`;
        
    return `
        <div class="photo-slot">
            <div class="photo-preview-box" id="preview-${slotId}">
                
                <div class="photo-display-zone">
                    ${imageHtml}
                </div>

                <div class="photo-controls">
                    <label for="input-${slotId}" class="btn-icon btn-edit" title="Modifier">
                        <i class="fa-solid fa-pen"></i>
                    </label>

                    <button type="button" class="btn-icon btn-delete" 
                            onclick="clearPhoto('${slotId}')" 
                            title="Supprimer"
                            style="${hasPhoto ? 'display:flex' : 'display:none'}">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </div>

            <input type="file" 
                   id="input-${slotId}"
                   name="${inputName}"
                   accept="image/*" 
                   style="display: none;"
                   onchange="previewPhoto(this, '${slotId}')">
        </div>
    `;
}