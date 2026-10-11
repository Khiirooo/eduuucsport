# PleinRadar - Belgique

Application autonome disponible dans le dossier `pleinradar/`. Le depot preexistant et ses autres projets ne sont pas modifies.

## Lancer et publier

- GitHub Actions > **PleinRadar - prix carburant (6h)** : une execution est lancee apres l'ajout des fichiers, puis toutes les six heures.
- GitHub Settings > Pages > Build and deployment > Source : **GitHub Actions** (activation initiale requise).
- Adresse apres mise en ligne : https://khiirooo.github.io/eduuucsport/pleinradar/

## Flux tarifaire

`pleinradar/scripts/update_pumperly.py` recupere `https://pumperly.com/api/stations`, valide la monnaie EUR, le pays BE et la date de remontée, puis publie les prix indicatifs dans `pleinradar/data/stations.json`. Sans tarifs recents confirmes par la source, aucun prix fictif n'est affiche. En cas d'echec, les anciennes donnees ne sont pas ecrasees. Les prix expirent a l'affichage au bout de 48 heures. API publique, pas de cle payante. Donnees Pumperly issues pour la Belgique d'ANWB; la licence de republication est a verifier avant toute exploitation publique/commerciale.

La mise a jour chaque six heures ne signifie pas prix instantanes des pompes.
