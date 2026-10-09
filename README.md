# desertpaintings.com

Small watercolors from Palm Springs and the surrounding desert, by Mark.

## How this works

You keep **one full-size image per painting or photo** in the `source` folder. When you change anything on GitHub, Amplify rebuilds the whole site automatically, in about two minutes. It makes every image size, the share previews, the sitemap, and the search data. You never edit the website files themselves.

```
source/
  paintings/        one image per painting, named <slug>.jpg
  photos/           one image per reference photo, named <slug>.jpg
  paintings.json    titles, sizes, dates, places, order on the site
  photos.json       reference photo titles, places, sections
  brand/            your portrait and the roadrunner icon
  build.py          the script Amplify runs (no need to touch it)
  site.css, site.js, analytics.js
amplify.yml         tells Amplify to run the build
customHttp.yml      caching and security settings
```

## Replace a painting with a new scan

1. Scan the painting at 300–600 dpi and save it as a **JPG under 25 MB**. Crop it to the edge of the card, or leave a little margin; either works.
2. Name it exactly like the file it replaces, for example `roadrunner-crossing.jpg`. The current names are below.
3. On GitHub, open `source/paintings`, click **Add file → Upload files**, drop in the new file, and click **Commit changes**. GitHub replaces the old file because the name matches.
4. Wait about two minutes. The site updates, and visitors see the new image right away.

You can replace several at once. A reference photo works the same way, in `source/photos`.

| Painting | File in source/paintings |
|---|---|
| Desert Wildflowers | desert-wildflowers.jpg |
| Summer Cloud, Palm Springs | summer-cloud-palm-springs.jpg |
| Hazey Day | hazey-day.jpg |
| Roadrunner Crossing | roadrunner-crossing.jpg |
| San Jacinto Purple Sky | san-jacinto-purple-sky.jpg |
| Clouds Over the San Jacintos | clouds-over-the-san-jacintos.jpg |
| Salton Sea, Still Morning | salton-sea-still-morning.jpg |
| Watchtower | watchtower.jpg |
| Rain, Rain | rain-rain.jpg |
| Desert Sun Over the Dunes | desert-sun-over-the-dunes.jpg |
| Monsoon Storm, San Jacinto | monsoon-storm-san-jacinto.jpg |
| Cloud Field Over the Foothills | cloud-field-san-jacinto-foothills.jpg |

## Small text changes

Titles, places, dates, notes and "Sold" live in `source/paintings.json`. On GitHub, open the file, click the pencil, edit the text between the quotes, and commit. Keep the quotes and commas as they are. Set `"available": false` to show a painting as Sold. Add a sentence in `"note"` and it appears on that painting's page.

## Adding new paintings

Send the photo or scan and the details to Claude. It adds the entry to `paintings.json` and the image to `source/paintings`, and gives you the files to upload.

## If a build fails

The site stays exactly as it was; nothing breaks for visitors. In Amplify, open the failed build and read the last lines of the log. The most common cause is an image name that doesn't match. The log says which file is missing, for example `Missing image: source/paintings/rain-rain.jpg`.

## Google Analytics

The ID is in `source/analytics.js`. Besides page views, it records email copies, YouTube clicks, filter use, and shares (`share` events, with the method: share sheet, copy link, or Pinterest).

## Amplify redirect rules

These are set in the Amplify console under **Hosting → Rewrites and redirects**:

```json
[
  { "source": "https://www.desertpaintings.com/<*>", "status": "301", "target": "https://desertpaintings.com/<*>" },
  { "source": "https://www.desertpaintings.com", "status": "301", "target": "https://desertpaintings.com" },
  { "source": "/<*>", "status": "404", "target": "/404.html" }
]
```
