-- ==============================
-- pour se connecter à MySQL sur Aiven
--mysql -h presence-dbeddb-projetbrown01.k.aivencloud.com -P 13995 -u avnadmin -p defaultdb
-- si on demande le mot de passe, c'est celui sur Aiven 
-- ==============================

-- ==============================
-- pour se connecter à MySQL en local
-- mysql -h localhost -P 3306 -u presenceapp -p gestion_presence
-- si on demande le mot de passe, c'est celui défini en local
-- ==============================

-- Nettoyage des tables existantes
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS presences;
DROP TABLE IF EXISTS visages;
DROP TABLE IF EXISTS employes;
DROP TABLE IF EXISTS utilisateurs;
SET FOREIGN_KEY_CHECKS = 1;

-- ==============================
-- Table des administrateurs
-- ==============================
CREATE TABLE utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'ADMIN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- Table des employés
-- ==============================
CREATE TABLE employes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    matricule VARCHAR(50) UNIQUE,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    poste VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- Table des visages (Images & Encodages)
-- ==============================
CREATE TABLE visages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employe_id INT NOT NULL,
    chemin_image VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    encodage JSON NOT NULL, -- Stocke les vecteurs faciaux
    type_vue ENUM('face', 'profil_gauche', 'profil_droit') NOT NULL,
    FOREIGN KEY (employe_id) REFERENCES employes(id) ON DELETE CASCADE
);

-- ==============================
-- Table des présences
-- ==============================
CREATE TABLE presences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employe_id INT NOT NULL,
    date_presence DATE NOT NULL,
    heure_arrivee TIME,
    heure_depart TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_employe_presence 
        FOREIGN KEY (employe_id) REFERENCES employes(id) ON DELETE CASCADE,
    CONSTRAINT unique_presence 
        UNIQUE (employe_id, date_presence)
);

