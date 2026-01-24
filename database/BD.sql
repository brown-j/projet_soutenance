
-- Création de la base de données
CREATE DATABASE IF NOT EXISTS gestion_presence;
USE gestion_presence;

-- Création de la table 'employés'
CREATE TABLE employes (
    ID_Employe INT(11) PRIMARY KEY,
    nom CHAR(30),
    prenom CHAR(20),
    position CHAR(20),
    photo LONGBLOB
);

-- Création de la table 'horodatage'
CREATE TABLE horodatage (
    IDhorodatage INT(11) PRIMARY KEY,
    ID_Employe INT(11),
    heure_entree TIME(6),
    heure_sortie TIME(6),
    date_jour DATE,
    FOREIGN KEY (ID_Employe) REFERENCES employes(ID_Employe)
);

-- Création de la table 'administrateurs'
CREATE TABLE administrateurs (
    ID_Admin INT(11) PRIMARY KEY,
    nom CHAR(30),
    prenom CHAR(20),
    role CHAR(20)
);

-- Création de la table 'configuration'
CREATE TABLE configuration (
    ID_config INT(11) PRIMARY KEY,
    parametre CHAR(20),
    valeur CHAR(20),
    lastUpdated DATETIME(6)
);

-- Création de la table 'systemlogs'
CREATE TABLE systemlogs (
    ID_logs INT(11) PRIMARY KEY,
    action CHAR(20),
    detail CHAR(70)
);


