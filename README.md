# CS2 Magyar Update Bot

Steam CS2 (App ID 730) híreket figyel, Gemini AI-val magyarra fordítja, majd valódi Discord botként elküldi a megadott csatornába.

## Fontos a gyorsaságról
GitHub Actions ütemezett workflow esetén a legrövidebb támogatott időköz 5 perc, és a futás terhelés miatt késhet. Ez nem garantál azonnali, másodperces értesítést. A teljesen folyamatos, 15–30 másodperces figyeléshez mindig futó host szükséges; az ingyenes hostok gyakran alvó módba kerülnek.

## Beállítás

### 1) Discord bot
1. Nyisd meg https://discord.com/developers/applications
2. Create Application, adj nevet.
3. Bot menü: Add Bot / Reset Token, másold ki a tokenedet (csak titkos helyre).
4. OAuth2 → URL Generator: `bot` scope, és `View Channel`, `Send Messages`, `Embed Links` jogosultság.
5. A generált URL-lel add hozzá a botot a szerveredhez.
6. Discord Developer Mode bekapcsolása: User Settings → Advanced → Developer Mode.
7. Célcsatorna jobb klikk → Copy Channel ID.

### 2) Gemini API-kulcs
1. Nyisd meg https://aistudio.google.com/app/apikey
2. Hozz létre API-kulcsot, ha a fiókod jogosult rá.
3. A Gemini API ingyenes kerete, modellhozzáférése és feltételei változhatnak; ellenőrizd a Google aktuális oldalán.
4. API-kulcsot ne ossz meg, ne tölts fel a repositoryba. Ha a fiók életkori feltételei miatt nem tudsz kulcsot létrehozni, kérj szülő/gondviselő segítséget, ne kerüld meg a feltételeket.

### 3) GitHub
1. Hozz létre egy új repository-t. Public repository esetén a GitHub-hosted standard Actions használata ingyenes.
2. Töltsd fel a ZIP fájljait, a `.github/workflows/check.yml` mappastruktúrát megtartva.
3. Repository → Settings → Secrets and variables → Actions → New repository secret.
4. Hozd létre ezeket a titkokat:
   - `DISCORD_BOT_TOKEN`
   - `DISCORD_CHANNEL_ID`
   - `GEMINI_API_KEY`
5. A workflow fájl legyen a repository alapértelmezett ágán (általában `main`).
6. Actions fül → `CS2 Magyar Update Bot` → Run workflow az első kézi futtatáshoz.

### Első futás
Első alkalommal a bot csak elmenti a legfrissebb hírazonosítót, régi híreket nem küld ki. Ezután az új híreket fordítja és küldi.

## Biztonság
- Tokeneket és API-kulcsokat csak GitHub Secrets-ben tárolj.
- Ha a Discord token valaha nyilvánosságra kerül, a Developer Portalon azonnal regeneráld.
- A bot nem figyel minden háttérben megváltozó játékfájlt; a Steam hivatalos híreket ellenőrzi.
