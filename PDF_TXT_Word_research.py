import os
import sys
import fitz  # PyMuPDF
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QMessageBox,
    QLineEdit,
    QProgressBar,
    QTabWidget,
    QTextBrowser,
    QLabel,
)
from collections import defaultdict


class PDFSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.history = []

    def initUI(self):
        self.setWindowTitle("Recherche de mots dans des PDF - Version 3")
        self.setGeometry(100, 100, 1400, 650)
        self.tab_widget = QTabWidget()

        self.setWindowIcon(QIcon("logoAXA.jpg"))
        
        # Premier onglet "Recherche"
        search_tab = QWidget()
        search_layout = QVBoxLayout(search_tab)

        search_input_layout = QHBoxLayout()
        self.keywordsInput = QLineEdit(self)
        self.keywordsInput.setPlaceholderText("Entrez vos mots à rechercher ici (séparés par des virgules)...")
        search_button = QPushButton("Rechercher", self)
        search_button.clicked.connect(self.searchPDFs)
        search_input_layout.addWidget(self.keywordsInput)
        search_input_layout.addWidget(search_button)

        self.pdfDisplay = QTextEdit(self)
        self.pdfDisplay.setReadOnly(True)
        
        select_layout = QHBoxLayout()
        self.selectButton = QPushButton("Sélectionner des PDF", self)
        self.selectButton.clicked.connect(self.selectPDFs)
        select_layout.addWidget(self.selectButton)
        search_layout.addLayout(search_input_layout)
        search_layout.addWidget(self.pdfDisplay)
        search_layout.addLayout(select_layout)

        select_folder_layout = QHBoxLayout()
        self.selectFolderButton = QPushButton("Sélectionner un dossier", self)
        self.selectFolderButton.clicked.connect(self.selectFolder)
        select_folder_layout.addWidget(self.selectFolderButton)
        select_folder_layout.addWidget(self.selectButton)
        search_layout.addLayout(select_folder_layout)
        
        self.resultText = QTextEdit(self)
        self.resultText.setReadOnly(True)
        search_layout.addWidget(self.resultText)
        progress_layout = QHBoxLayout()

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("", self)  
        progress_layout.addWidget(self.progress_label) 

        search_layout.addLayout(progress_layout)
        search_tab.setLayout(search_layout)

        # Deuxième onglet "Historique"
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        
        search_and_clean_layout = QHBoxLayout()
        self.search_history_edit = QLineEdit(self)
        self.search_history_edit.setPlaceholderText("Rechercher dans l'historique...")
        self.search_history_edit.textChanged.connect(self.filterHistory)
        search_and_clean_layout.addWidget(self.search_history_edit) 
        clean_history_button = QPushButton("Nettoyer l'historique", self)
        clean_history_button.setMaximumWidth(300)
        clean_history_button.clicked.connect(self.cleanHistory)
        search_and_clean_layout.addWidget(clean_history_button)
        history_layout.addLayout(search_and_clean_layout)
        self.historyTextBrowser = QTextBrowser(self)
        history_layout.addWidget(self.historyTextBrowser)
        history_tab.setLayout(history_layout)

        # Troisième onglet "Aide"
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)
        self.initHelpTab(help_layout)  # Appel de la méthode pour créer le contenu de l'onglet d'aide
        help_tab.setLayout(help_layout)

        self.tab_widget.addTab(search_tab, "Recherche")
        self.tab_widget.addTab(history_tab, "Historique")
        self.tab_widget.addTab(help_tab, "?")

        self.history = {}
        self.setCentralWidget(self.tab_widget)

    def selectPDFs(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Sélectionner des fichiers PDF", "", "PDF Files (*.pdf)", options=options
        )
        if file_paths:
            self.pdf_files = file_paths
            self.pdfDisplay.clear()
            for pdf_file in self.pdf_files:
                self.pdfDisplay.append(f"{os.path.abspath(pdf_file)}")

    def selectFolder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier contenant des PDF")
        if folder_path:
            self.pdf_files = self.get_pdf_files_in_folder(folder_path)
            self.pdfDisplay.clear()
            for pdf_file in self.pdf_files:
                self.pdfDisplay.append(f"{os.path.abspath(pdf_file)}")

    def get_pdf_files_in_folder(self, folder_path):
        pdf_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".pdf"):
                    pdf_files.append(os.path.join(root, file))
        return pdf_files

    def addSearchToHistory(self, keywords, results):
        keywords_text = ", ".join(keywords)
        self.history.append({"keywords": keywords_text, "results": results})
        self.historyTextBrowser.append(f"Recherche: {keywords_text}")
        for keyword, documents in results.items():
            self.historyTextBrowser.append(f"{keyword} :")
            for document, pages in documents.items():
                page_list = ', '.join([str(page) for page in pages])
                self.historyTextBrowser.append(f"{document} - pages {page_list}")
            if not results:
                self.historyTextBrowser.append(f"{keyword} - Le mot n'a pas été trouvé")
            self.historyTextBrowser.append("")
        self.generateHTMLHistory()  # Appelez la méthode pour mettre à jour l'historique HTML

    def generateHTMLHistory(self):
        # Définir le style CSS pour améliorer la mise en page
        css_style = """
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            h2 {
                font-size: 20px;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            h3 {
                font-size: 18px;
                margin-top: 10px;
                margin-bottom: 5px;
            }
            p {
                margin-bottom: 10px;
            }
            a {
                text-decoration: none;
                color: #007BFF;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
        """
    
        html_content = f"<html><head><title>Historique de Recherche</title>{css_style}</head><body>"
        for entry in self.history:
            keywords_text = entry["keywords"]
            results = entry["results"]
            html_content += f"<h2>Recherche: {keywords_text}</h2>"
            for keyword, documents in results.items():
                html_content += f"<h3>{keyword}</h3>"
                for document, pages in documents.items():
                    file_link = f"file://{document.replace(' ', '%20')}"
                    html_content += f"<p><a href='{file_link}' target='_blank'>{os.path.basename(document)}</a> - Pages {', '.join(map(str, pages))}</p>"
        html_content += "</body></html>"
        
        with open("history.html", "w", encoding="utf-8") as html_file:
            html_file.write(html_content)

    def cleanHistory(self):
        self.historyTextBrowser.clear()

    def filterHistory(self):
        search_text = self.search_history_edit.text().strip().lower()
    
        self.historyTextBrowser.clear()
    
        for entry in self.history:
            keywords_text = entry["keywords"]
            results = entry["results"]
    
            if search_text in keywords_text.lower() or any(search_text in keyword.lower() for keyword in results.keys()):
                self.historyTextBrowser.append(f"Recherche : {keywords_text}")
                for keyword, documents in results.items():
                    self.historyTextBrowser.append(f"{keyword} :")
                    for document, pages in documents.items():
                        page_list = ', '.join([str(page) for page in pages])
                        self.historyTextBrowser.append(f"{document} - pages {page_list}")
                    if not documents:
                        self.historyTextBrowser.append(f"{keyword} - Le mot n'a pas été trouvé")
                self.historyTextBrowser.append("")

    def displayFullHistory(self):
        self.historyTextBrowser.clear()
        for entry in self.history:
            keywords_text = entry["keywords"]
            results = entry["results"]
            self.addToHistoryText(keywords_text, results)

    def displayFilteredHistory(self, filtered_history):
        self.historyTextBrowser.clear()

        for entry in filtered_history:
            keywords_text = entry["keywords"]
            results = entry["results"]
    
            self.historyTextBrowser.append(f"Recherche : {keywords_text}")
            for keyword, documents in results.items():
                self.historyTextBrowser.append(f"{keyword} :")
                for document, pages in documents.items():
                    page_list = ', '.join([str(page) for page in pages])
                    self.historyTextBrowser.append(f"{document} - pages {page_list}")
                if not documents:
                    self.historyTextBrowser.append(f"{keyword} - Le mot n'a pas été trouvé")
                self.historyTextBrowser.append("")
    
    def addToHistoryText(self, keywords_text, results):
        self.historyTextBrowser.append(f"Recherche: {keywords_text}")
        for keyword, documents in results.items():
            self.historyTextBrowser.append(f"{keyword} :")
            for document, pages in documents.items():
                page_list = ', '.join([str(page) for page in pages])
                self.historyTextBrowser.append(f"{document} - pages {page_list}")
            if not results:
                self.historyTextBrowser.append(f"{keyword} - Le mot n'a pas été trouvé")
            self.historyTextBrowser.append("")
        self.generateHTMLHistory()
            
    def searchPDFs(self):
        if not hasattr(self, "pdf_files"):
            self.showMessageBox("Aucun PDF sélectionné", "Veuillez sélectionner des fichiers PDF à rechercher.")
            return

        keywords_text = self.keywordsInput.text().strip()
        if not keywords_text:
            self.showMessageBox("Aucun mot", "Veuillez entrer au moins un mot à rechercher.")
            return

        self.resultText.clear()
        keywords = [keyword.strip() for keyword in keywords_text.split(",") if keyword.strip()]

        found_results = {}
        total_files = len(self.pdf_files)
        current_file = 0

        for pdf_file in self.pdf_files:
            current_file += 1
            pdf_path = os.path.abspath(pdf_file)
            try:
                pdf = fitz.open(pdf_path)
            except FileNotFoundError as e:
                error_message = f"Erreur : Le fichier PDF suivant n'a pas pu être trouvé :\n{pdf_path}"
                self.resultText.append(error_message)
                continue

            file_found = False

            for keyword in keywords:
                if keyword not in found_results:
                    found_results[keyword] = {}
                for page_num in range(len(pdf)):
                    page = pdf[page_num]
                    text = page.get_text()
                    if keyword.lower() in text.lower():
                        file_found = True
                        if pdf_path not in found_results[keyword]:
                            found_results[keyword][pdf_path] = []
                        found_results[keyword][pdf_path].append(page_num + 1)

            if not file_found:
                if all(char.isspace() or char == "" for char in pdf[0].get_text()):
                    not_found_message = f"{os.path.basename(pdf_path)} : ce fichier est vide\n"
                    self.resultText.append(not_found_message)

            progress_value = (current_file / total_files) * 100
            self.progress_bar.setValue(int(progress_value))
            self.progress_label.setText(f"{current_file}/{total_files}")

            QApplication.processEvents()

        self.addSearchToHistory(keywords, found_results)

        for keyword, results in found_results.items():
            self.resultText.append(f"{keyword} :")
            for pdf_name, pages in results.items():
                page_list = ", ".join([str(page) for page in pages])
                self.resultText.append(f"{os.path.basename(pdf_name)} - pages {page_list}")
            if not results:
                self.resultText.append(f"{keyword} - Le mot n'a pas été trouvé")
            self.resultText.append("")

        self.progress_bar.setValue(0)
        self.progress_label.setText("")

    def initHelpTab(self, layout):
        help_text = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    font-size: 16px;
                    margin: 20px;
                }
                h2 {
                    font-size: 20px;
                }
                ol {
                    list-style-type: decimal;
                    margin-left: 20px;
                }
            </style>
        </head>
        <body>
            <h2>Bienvenue dans l'application de recherche de mots dans des fichiers PDF !</h2>
            <p>Cette application vous permet de rechercher des mots-clés dans des fichiers PDF. Vous pouvez sélectionner des fichiers PDF individuels ou un dossier entier pour effectuer des recherches.</p>
            <p><strong>Onglet "Recherche" :</strong></p>
            <ol>
                <li>Cliquez sur le bouton "Sélectionner des PDF" pour choisir les fichiers PDF à rechercher ou "Sélectionner un dossier" pour rechercher dans un dossier et ses sous-dossiers.</li>
                <li>Entrez les mots-clés dans le champ de texte, séparés par des virgules.</li>
                <li>Cliquez sur "Rechercher" pour lancer la recherche.</li>
                <li>Les résultats s'afficheront ci-dessous.</li>
            </ol>
        
            <p><strong>Onglet "Historique" :</strong></p>
            <ul>
                <li>Consultez les résultats précédents et filtrez-les en utilisant la barre de recherche.</li>
                <li>Cliquez sur le lien du document pour l'ouvrir dans votre visionneuse PDF par défaut.</li>
                <li>Nettoyez l'historique en cliquant sur "Nettoyer l'historique".</li>
            </ul>
        
            <p><strong>Remarques :</strong></p>
            <ul>
                <li>Les fichiers PDF dits "vides" sont sous format d'images et ne peuvent pas être traités comme les autres documents. Vous pouvez utiliser un programme OCR pour extraire le texte de ces fichiers.</li>
                <li>Lors de la sélection d'un dossier, tous les PDF dans le dossier et les sous-dossiers seront recherchés.</li>
            </ul>
        
            <p>Version du 20.09.2023</p>
        </body>
        </html>
        """
        help_browser = QTextBrowser(self)
        help_browser.setOpenExternalLinks(True)
        help_browser.setHtml(help_text)
        layout.addWidget(help_browser)

    def showMessageBox(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()

def main():
    app = QApplication(sys.argv)
    window = PDFSearchApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
