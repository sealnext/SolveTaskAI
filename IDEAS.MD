1. Creare de task-uri complexe

Orchestrator: Primește cererea: "Creează un proiect pentru dezvoltarea acestui nou feature, imparte in subtaskuri si pune estimari. Feature-ul este .... "
Workers: Creează un epic principal, adaugă subtask-uri pentru analiză, dezvoltare, QA și documentație, atribuie utilizatori, deadline-uri și estimări.
Synthesizer: Verifică dacă totul este complet și oferă un rezumat utilizatorului, cu fiecare link catre task-uri.


2.Gestionare incidente

Agentul: Primește rapoarte de erori din loguri sau alerte, automat din alte parti.
Workers: Creează automat un ticket Bug, populează descrierea cu detalii tehnice, adaugă etichete critice (ex: "Critical", "P1") și notifică echipa relevantă. Dar si cauta in documente daca a fost deja un incident asemanator,
da sfaturi si linkuieste la incidente asemanatoare.

3. Analiză backlog

Agentul: Primește cererea: "Analizează backlog-ul și sugerează task-uri pentru dezvoltare."
Orchestrator: Primește cererea: "Prioritizează backlog-ul pentru sprint-ul următor."
Workers: Sortează task-urile după prioritate și complexitate, mută cele esențiale în sprint, identifică task-uri blocate și creează un raport.
Synthesizer: Propune prioritizări și oferă o vedere de ansamblu pentru echipă, ce ar trebui fiecare sa faca si cand si cum si esteimari


4. Ședințe retrospective

Orchestrator: Solicită analiza task-urilor finalizate și celor blocate.
Workers: Extrage date despre timpul efectiv vs. estimat, identifică blocaje și creează un document cu lecții învățate.
Synthesizer: Compune un raport complet pentru retrospective și îl distribuie echipei.

5. Curățare backlog

Orchestrator: Identifică task-uri stagnante (ex: neactualizate de 90+ zile).
Workers: Notifică utilizatorii, le cere feedback si le cere sa actualizeze task-ul, automat.
Synthesizer: Rezumă acțiunile efectuate într-un raport detaliat.

6. Triage tickete

Orchestrator: Primește tickete noi și organizează fluxul.
Workers: Categorizează ticket-ul (ex: Bug, Feature, Improvement), adaugă etichete relevante și atribuie persoanei potrivite
Intai pentru fiecare persoana din echipa se verifica ce task-uri au facut deja, si daca se aseamana
cu task-ul nou, se atribuie automat, aici s-ar face retrieve la toate task-urile facute de un anumit user.
Si se face un rezumat of strenghts and weaknesses.
Synthesizer: Confirmă asignările și oferă un raport pentru manageri, si spune de ce fiecare user ar trebui sa faca task-ul nou.

7. Generare documentație

Orchestrator: Solicită documentație pentru task-urile din cadrul unui epic. 
Workers: Adună informații (pași, commit-uri, teste), taskuri, comments, etc.
creează documentația și o atașează în Jira.
Synthesizer: Verifică documentația și notifică echipa.