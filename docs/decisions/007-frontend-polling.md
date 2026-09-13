# Frontend polling plutôt que websocket

**Décision :** le statut des scans est rafraîchi par **polling HTTP** (`GET /scans` et `GET /scans/{id}` toutes les 2 s tant que le statut est `pending` ou `running`).

**Pourquoi pas de websocket :** un scan Semgrep/OSV tient des secondes à une minute. Un canal WS ajouterait un serveur, un protocole, et des tests de reconnexion pour un événement qui a quatre états. Rien dans le harnais Phase 3 ni dans le débit de scans ne justifie ce coût.

Le client s’arrête de poller dès que le scan est `completed` ou `failed`. CORS est ouvert sur Vite (`http://localhost:5173`).
