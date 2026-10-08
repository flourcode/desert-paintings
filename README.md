# desertpaintings.com

Small watercolors from Palm Springs and the surrounding desert, by Mark.

This is a plain static website: HTML, one stylesheet, two small scripts, and images. There is no build step, so AWS Amplify serves the files exactly as they are.

## What's in here

| Path | What it is |
|---|---|
| `index.html` | Home page |
| `paintings/` | The full index, with place filters |
| `roadrunner-crossing/` and the other painting folders | One page per painting |
| `about/`, `videos/` | About (with contact and common questions) and Videos |
| `404.html` | Page shown for a missing address |
| `images/` | Paintings (full size and 800px versions) and social share images in `images/og/` |
| `assets/site.css`, `assets/site.js` | Styles, place filters and the copy-email button |
| `assets/analytics.js` | Google Analytics. Does nothing until you add your ID |
| `sitemap.xml`, `robots.txt` | For search engines |
| `llms.txt` | Plain-text summary of the site for AI answer engines |
| `favicon.ico`, `*.png`, `site.webmanifest` | Browser and phone icons |
| `amplify.yml`, `customHttp.yml` | Amplify settings: no build, security and caching headers |

## Put it on GitHub

1. Create a new repository on GitHub (for example `desertpaintings`).
2. Upload everything in this folder to the root of the repository, keeping the folders as they are. Using the GitHub website: **Add file → Upload files**, drag the contents of this folder in, then **Commit changes**.

## Connect AWS Amplify

1. In the AWS console, open **Amplify** → **Create new app** → **GitHub**, and pick this repository and the `main` branch.
2. Amplify reads `amplify.yml` and sees there is no build. Accept the defaults and deploy.
3. **Hosting → Custom domains → Add domain** → `desertpaintings.com`. Let Amplify set up both `desertpaintings.com` and `www`, with `www` redirecting to `desertpaintings.com`. If the domain is in Route 53, Amplify adds the DNS records for you. Otherwise it shows you records to add at your registrar.
4. **Hosting → Rewrites and redirects → Manage redirects → Open text editor**, and paste:

```json
[
  { "source": "https://www.desertpaintings.com", "target": "https://desertpaintings.com", "status": "301", "condition": null },
  { "source": "/<*>", "target": "/404.html", "status": "404", "condition": null }
]
```

The first rule sends `www` to the main address. The second shows the 404 page for any address that doesn't exist.

## Turn on Google Analytics

1. In Google Analytics, create a GA4 property with a web stream for `https://desertpaintings.com`.
2. Copy the Measurement ID (`G-XXXXXXXXXX`).
3. Open `assets/analytics.js` on GitHub, click the pencil to edit, paste the ID between the quotes on the line `var GA_MEASUREMENT_ID = "";`, and commit.

Amplify redeploys within a minute or two. Besides page views, it records email copies, YouTube link clicks, and use of the place filters.

## After it's live

1. **Google Search Console**: add `https://desertpaintings.com` as a property, verify it (the DNS option is easiest), then submit `https://desertpaintings.com/sitemap.xml`.
2. **Bing Webmaster Tools**: import the property from Search Console and submit the same sitemap. Bing's index also feeds several AI answer engines.
3. **YouTube**: in the channel's About section, link to `https://desertpaintings.com`. The site already links back to the channel.

## Changing things later

Small text fixes can be made directly in the HTML files on GitHub. For new paintings, notes, prices or sold originals, ask Claude to rebuild the site, so every page, the sitemap and the structured data stay in step.
