- make /refresh endpoint work, for now we don't use it
    - either by calling from the frontend every time the token expires
    - or automatically by the backend when the token is expired
- make the chat more responsive
- make log out instantly, don't wait for the server response
- implement the login/signup with google and github
- add the frontend into the docker compose
- fix frontend bugs
    - when double clicking on the profile icon, the dropdown doesn't close
    - make the checkbox on the login more aesthetic, also make it work, for now by default is checked even if the user didn't check it, because the server always send an refresh token
    - test if the token expires the user will be redirected to the login page or can still access the app
    - change the login/register hover color to be more subtle
    - make the send button from chat, to dont hide when is loading 
    - the dark mode options is not aligned with the other options
    - delete full names restriction, it was a username before but now is a full name.
    maybe try to sanitize it, escape it, and be carefull in the backend to be parameterized query, not
    sure if its by default, just need to check that so we wont allow any sql injection or script execution
    - make login and signup  errors more contrastful

- backend
    - make a table for revoked tokens, don't save them in memory
    - scoate "created_at", si "permissions" din APIKey
    

- The Confluence space key may not always be the same as the Jira project key, but in my case, it is the same, specifically "PZ." Ideally, from the web app, there should be a way to check if a Confluence space with the same name exists. If it doesn't, you should have the option to add different Confluence spaces linked to a Jira project, or be able to select various Confluence spaces directly from the web and join them with a Jira project when performing a search. For the moment we just assume that the confluence space key is the same as the jira project key and when we do the embeddings we use the jira project key to find the confluence space.

eu cand am schimbat din jira project sa leg alt confluence space, acel confluence space nou creat avea PA .. deci nu mereu coincide cu project key-ul din Jira.

- atunci cnad un user vrea sa stearga un proiect, nu ar trebui by defualt sa stergem datele din vector store, doar sa stergem legatura dintre acel user si proiect. Daca sunt 0 legaturi intre proiect si alti useri, doar atunci se pot sterge totul.

- sa fie mereu https cand se adauga un proiect, sa nu fie si http si https pentru acelasi domeniu. Ma gandesc ca 
http nu are rost ca oricum nu e un safe protocol.

- ar trebui sa mutam logica de data_extractor in ruta, sa putem trimite inapoi la frontend si cat o sa dureze sa se faca embedding-urile. Momentan logica e facuta in nodes.py si se face doar in backend.
Un plus aici ar fi sa nu supraincarcam state-ul cu toate documentele de odata, doar cu batch-uri de 50 de documente sau cat e nevoie si setat in data_extractor.

Deduplication: Avoid embedding already existing tickets.

Batching: Process embeddings and insertions in batches to improve performance.

Efficient Metadata Updates: Update metadata without re-embedding tickets.

Enhanced Logging: Improve logging for tracking and error handling.

- check if the delete_embeddings is not deleting the embeddings if 2 users have the same project

- cache the pgvector so we dont need to create a new connection every time

- if no context is found at retrieval, try to make multiple generations of the same questions, and retrieve again, until we find context or we run out of generations.

- Instead of using the original user question as a query to the database, it is typical to rewrite the question for optimized retrieval. For example, we can use the HyDE method.

- foloseste ensure_config in loc de state in graph pentru
a salvat date sensitive, deoarece state e salvat in memory la un moment dat.

- foloseste checkpoint la graph pentru a fi salvat in baza de date si sa nu se mai piarda chat-ul.