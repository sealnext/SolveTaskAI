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