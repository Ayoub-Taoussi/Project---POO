import numpy as np
import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.request import urlretrieve

class base_livre:
  def __init__(self,ressource):
    self.ressource = ressource

  def type(self):
    """ renvoie le type (EPUB, PDF, ou autre) du livre """
    raise NotImplementedError("à définir dans les sous-classes")

  def titre(self):
    """ renvoie le titre du livre """
    raise NotImplementedError("à définir dans les sous-classes")

  def auteur(self):
    """ renvoie l'auteur du livre """
    raise NotImplementedError("à définir dans les sous-classes")

  def langue(self):
    """ renvoie la langue du livre """
    raise NotImplementedError("à définir dans les sous-classes")

  def sujet(self):
    """ renvoie le sujet du livre """
    raise NotImplementedError("à définir dans les sous-classes")

  def date(self):
    """ renvoie la date de publication du livre """
    raise NotImplementedError("à définir dans les sous-classes")
##################################################################################

class base_bibli:
  def __init__(self,path):
    """ path désigne le répertoire contenant les livres de cette bibliothèque """
    raise NotImplementedError("à définir dans les sous-classes")

  def ajouter(self,livre):
    """
      Ajoute le livre à la bibliothèque """
    raise NotImplementedError("à définir dans les sous-classes")

  def rapport_livres(self,format,fichier):
    """
        Génère un état des livres de la bibliothèque.
        Il contient la liste des livres,
        et pour chacun d'eux
        son titre, son auteur, son type (PDF ou EPUB), et le nom du fichier correspondant.

        format: format du rapport (PDF ou EPUB)
        fichier: nom du fichier généré
    """
    raise NotImplementedError("à définir dans les sous-classes")

  def rapport_auteurs(self,format,fichier):
    """
        Génère un état des auteurs des livres de la bibliothèque.
        Il contient pour chaque auteur
        le titre de ses livres en bibliothèque et le nom du fichier correspondant au livre.
        le type (PDF ou EPUB),
        et le nom du fichier correspondant.

        format: format du rapport (PDF ou EPUB)
        fichier: nom du fichier généré
    """
    raise NotImplementedError("à définir dans les sous-classes")

################# Créer les sous-classes de base_livre utiles et nécessaires à l’application

class LivreEPUB(base_livre):
    def __init__(self, ressource, titre, auteur, langue, sujet, date_publication):
        super().__init__(ressource)
        self._titre = titre
        self._auteur = auteur
        self._langue = langue
        self._sujet = sujet
        self._date_publication = date_publication

    def type(self):
        return "EPUB"

    def titre(self):
        return self._titre

    def auteur(self):
        return self._auteur

    def langue(self):
        return self._langue

    def sujet(self):
        return self._sujet

    def date(self):
        return self._date_publication

##################################################
class LivrePDF(base_livre):
    def __init__(self, ressource, titre, auteur, langue, sujet, date_publication):
        super().__init__(ressource)
        self._titre = titre
        self._auteur = auteur
        self._langue = langue
        self._sujet = sujet
        self._date_publication = date_publication

    def type(self):
        return "PDF"

    def titre(self):
        return self._titre

    def auteur(self):
        return self._auteur

    def langue(self):
        return self._langue

    def sujet(self):
        return self._sujet

    def date(self):
        return self._date_publication


#################### Créer une sous-classe simple_bibli de base_bibli:
class simple_bibli(base_bibli):
    def __init__(self, path):
        self.path = path
        self.livres = []

    def ajouter(self, livre):
        # Ajoute le livre à la bibliothèque
        self.livres.append(livre)

    def rapport_livres(self, format, fichier):
        # Génère un rapport sur les livres de la bibliothèque
        with open(fichier, 'w') as rapport:
            rapport.write(f"Liste des livres de la bibliothèque au format :\n")
            for livre in self.livres:
                rapport.write(f"Titre: {livre.titre()}, Auteur: {livre.auteur()}, Type: {livre.type()}, Fichier: {livre.ressource}\n")

    def rapport_auteurs(self, format, fichier):
        # Génère un rapport sur les auteurs des livres de la bibliothèque
        auteurs = {}
        with open(fichier, 'w') as rapport:
            rapport.write(f"Liste des auteurs des livres de la bibliothèque :\n")
            for livre in self.livres:
                auteur = livre.auteur()
                if auteur not in auteurs:
                    auteurs[auteur] = []
                auteurs[auteur].append(f"Titre: {livre.titre()}, Type: {livre.type()}, Fichier: {livre.ressource}\n")
            
            for auteur, livres in auteurs.items():
                rapport.write(f"Auteur: {auteur}\n")
                rapport.write("".join(livres))

###################################### Créer une nouvelle classe bibli

class Bibli(simple_bibli):
    def __init__(self, path):
        super().__init__(path)
        self.livres = []

    def ajouter(self, livre):
        self.livres.append(livre)

    def alimenter(self,url):
        page = requests.get("https://math.univ-angers.fr/~jaclin/biblio/livres/", verify=False)
        titre = []
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, 'lxml')
            balises_livres = soup.find_all('tr')
            for balise_livre in balises_livres:
               link = balise_livre.a
               if link is not None:
                    titre.append(link["href"])
                    if link["href"].endswith("pdf"):
                        livre = LivrePDF(url+link["href"],link["href"], "unknown", "unknown", "unknown", datetime(2022, 1, 1))
                        self.ajouter(livre)
                    elif link["href"].endswith("epub"):
                        livre = LivreEPUB(url+link["href"],link["href"], "unknown", "unknown", "unknown", datetime(2022, 1, 1))
                        self.ajouter(livre)
     
###################################### Créer une nouvelle classe bibli_scrap

class BibliScrap:
    def __init__(self):
        self.downloaded_docs = 0
        self.session = requests.Session()
        self.livres = []

    def scrap(self, url, profondeur, nbmax):
        # Vérifier les conditions d'arrêt
        self.nbmax = nbmax
        if profondeur <= 0 or self.downloaded_docs >= self.nbmax :
            return

        try:
            # Télécharger la page web
            response = self.session.get(url,verify=False)
            response.raise_for_status()  # Gérer les erreurs HTTP

            soup = BeautifulSoup(response.text, 'html.parser')

            # Télécharger les documents PDF et EPUB
            self.download_documents(soup,url)

            # Extraire les liens vers d'autres pages web HTML
            links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True) if self.is_html_link(a)]

            # Réitérer le processus pour chaque lien
            for link in links:
                self.scrap(link, profondeur - 1, self.nbmax)
        except requests.exceptions.RequestException as e:
            print(f"Une erreur s'est produite lors du traitement de {url}: {str(e)}")

    def is_html_link(self, a_tag):
        # Vérifier si le lien pointe vers une page HTML (Content-Type)
        href = a_tag.get('href', '')
        try:
            response = self.session.head(href)
            content_type = response.headers.get('content-type', '').lower()
            return content_type.startswith('text/html')
        except requests.exceptions.RequestException:
            return False

    def download_documents(self, soup,url):
        # Télécharger les documents PDF et EPUB
        response = self.session.get(url)
        response.raise_for_status()
        for link in soup.find_all('a', href=True):
            if self.downloaded_docs >= self.nbmax:
                return

            href = link['href']
            if href.endswith('.pdf') or href.endswith('.epub'):
                self.downloaded_docs += 1
                file_name = f"downloaded_file_{self.downloaded_docs}.{href.split('.')[-1]}"
                urlretrieve(urljoin(url,href), file_name)
                print(f"Téléchargement réussi : {file_name}")

###################################################################

if __name__ == "__main__":
    # Création d'une instance de Bibli
    bibli = Bibli(r"C:\Users\Utilisateur\Downloads\Biblio")

    # Création d'instances de LivreEPUB et LivrePDF
    livre_epub = LivreEPUB(r"C:\Users\Utilisateur\Downloads\Biblio\pdf.txt", "Titre EPUB", "Auteur EPUB", "Français", "Science Fiction", datetime(2022, 1, 1))
    livre_pdf = LivrePDF(r"C:\Users\Utilisateur\Downloads\Biblio\Ebook.txt", "Titre PDF", "Auteur PDF", "Anglais", "Informatique", datetime(2022, 2, 1))

    # Ajout des livres à la bibliothèque
    bibli.ajouter(livre_epub)
    bibli.ajouter(livre_pdf)

    # Génération de rapports
    bibli.rapport_livres("PDF", r"C:\Users\Utilisateur\Downloads\rapport_livres.txt")
    bibli.rapport_auteurs("EPUB", r"C:\Users\Utilisateur\Downloads\rapport_auteurs.txt")

    # Alimenter la bibliothèque depuis une URL
    bibli.alimenter("https://math.univ-angers.fr/~jaclin/biblio/livres/")

    # Vous pouvez maintenant accéder aux livres ajoutés à la bibliothèque
    for livre in bibli.livres:
        print(f"Titre: {livre.titre()}, Auteur: {livre.auteur()}, Type: {livre.type()}")
    Bibli2 = Bibli(r"C:\Users\Utilisateur\Downloads\Biblio")
    Bibli2.alimenter("https://math.univ-angers.fr/~jaclin/biblio/livres/")
    Bibli2.rapport_livres("PDF", r"C:\Users\Utilisateur\Downloads\rapport_livres.txt")
    Bibli2.rapport_auteurs("EPUB", r"C:\Users\Utilisateur\Downloads\rapport_auteurs.txt")

    # Exemple d'utilisation de BibliScrap
    d = BibliScrap()
    d.scrap("https://math.univ-angers.fr/~jaclin/biblio/livres/", profondeur=2, nbmax=5)
