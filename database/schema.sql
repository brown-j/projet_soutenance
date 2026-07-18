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
DROP TABLE IF EXISTS visages;
DROP TABLE IF EXISTS employes;
DROP TABLE IF EXISTS utilisateurs;
DROP TABLE IF EXISTS pointages;
DROP TABLE IF EXISTS notification_config;
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
    email VARCHAR(150) UNIQUE, -- NOUVEAU : Champ pour stocker l'adresse mail
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
-- Table pointages
-- ==============================
CREATE TABLE pointages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employe_id INT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    type_action ENUM('ENTREE', 'SORTIE', 'PASSAGE') DEFAULT 'PASSAGE',
    FOREIGN KEY (employe_id) REFERENCES employes(id)
);

-- ==============================
-- Table de configuration des notifications automatiques
-- ==============================

CREATE TABLE notification_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type_notification VARCHAR(50) DEFAULT 'Rapport de Présence',
    cron_minute VARCHAR(10) DEFAULT '0',
    cron_hour VARCHAR(10) DEFAULT '18',
    cron_day_of_week VARCHAR(20) DEFAULT '*', 
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    is_active TINYINT(1) DEFAULT 1
);


CREATE TABLE historique_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employe_id INT,
    email VARCHAR(255),
    statut ENUM('Succès', 'Échec') NOT NULL,
    message_erreur TEXT,
    date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employe_id) REFERENCES employes(id) ON DELETE CASCADE
);