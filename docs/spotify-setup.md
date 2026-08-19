# Optional Spotify card

The profile contains a static Spotify panel by default. The optional workflow
can replace it with your most recently played track using Spotify's official
OAuth API.

The workflow is disabled until the repository variable `SPOTIFY_ENABLED` is
set to `true`. It reads only `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and
`SPOTIFY_REFRESH_TOKEN` from GitHub Actions secrets.

The credential pasted into chat must be revoked or rotated before use. Never
put a client secret, refresh token, or access token in this repository.

To enable it, create a Spotify Developer application, use Authorization Code
flow with only `user-read-recently-played`, add the three repository secrets,
set `SPOTIFY_ENABLED=true`, and run the workflow once manually.
