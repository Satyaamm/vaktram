# Logo + favicon assets

Drop your two source PNGs at the paths below. Once they're in place,
nav, auth pages, and browser tabs all pick them up automatically — no
code changes, no manual favicon conversion.

## What goes where

| File path | Used by | Recommended size |
|---|---|---|
| `apps/web/public/logo-long.png` | The horizontal wordmark in nav and auth-page brand panel | ~480×80 px (transparent bg) |
| `apps/web/public/logoshort.png` | The square mark used as the badge in compact contexts | ~256×256 px (transparent bg) |
| `apps/web/src/app/icon.png` | Browser tab favicon (Next.js auto-generates favicons from this) | 512×512 px |
| `apps/web/src/app/apple-icon.png` | iOS home-screen icon | 180×180 px |

The `icon.png` and `apple-icon.png` can be the same file as `logoshort.png`
— Next.js resizes for you. The simplest workflow is to copy `logoshort.png`
into all three locations.

> The default Next.js favicon.ico (the Vercel triangle) has been removed.
> Until you drop the files above, browsers will show an unbranded blank
> tab — that's intentional, better than someone else's logo.

## After dropping the files

```bash
# Quick check
ls apps/web/public/logo-long.png apps/web/public/logoshort.png \
   apps/web/src/app/icon.png apps/web/src/app/apple-icon.png

# Then commit
git add apps/web/public apps/web/src/app/icon.png apps/web/src/app/apple-icon.png
git commit -m "chore: add brand assets"
git push
```

Vercel auto-deploys on push and your favicon updates everywhere.

## If you only have a square logo

Copy it into all four paths above. Next.js will scale it for the
favicon and apple-icon variants. The horizontal wordmark slot will
just show the square logo until you generate a proper long version.
