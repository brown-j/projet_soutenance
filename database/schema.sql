-- Création de la base de données
CREATE DATABASE IF NOT EXISTS gestion_presence;
USE gestion_presence;

-- ==============================
-- Table des utilisateurs (Admin)
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
    photo_reference VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- Table des visages (images)
-- ==============================
CREATE TABLE visages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employe_id INT NOT NULL,
    chemin_image VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    CONSTRAINT fk_employe
        FOREIGN KEY (employe_id) REFERENCES employes(id) ON DELETE CASCADE,
    CONSTRAINT unique_presence UNIQUE (employe_id, date_presence)
);
