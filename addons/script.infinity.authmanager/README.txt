INFINITY AUTHORIZATION MANAGER 0.1.0

Purpose:
- One Infinity-owned status/launch surface for account authorizations.
- Delegates real authorization to installed service owners.
- Does not copy, store, export, log, or display OAuth credentials.

Account Manager Lite 1.1.6 integration:
- Trakt: traktAuth / traktReSync / traktViewer
- Real-Debrid: realdebridAuth / realdebridReSync / realdebridViewer
- Premiumize, All-Debrid, TorBox, OffCloud, Easynews, MDBList supported similarly.

Persistence:
- special://profile/addon_data/script.infinity.authmanager/authorization-state.json
- Contains only status labels, booleans and timestamps. No token values.
